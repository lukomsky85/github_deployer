# utils/hooks.py
"""
Pre/Post deploy хуки — запуск пользовательских скриптов до и после пуша.
"""
import os
import json
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Callable


HOOKS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'hooks.json'
)


@dataclass
class Hook:
    id:       str
    name:     str
    type:     str          # 'pre' | 'post'
    command:  str          # команда/скрипт
    enabled:  bool = True
    timeout:  int  = 60    # секунды
    stop_on_fail: bool = True   # остановить деплой если хук упал (только для pre)
    last_exit_code: int = -1
    last_output:    str = ''

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'name': self.name, 'type': self.type,
            'command': self.command, 'enabled': self.enabled,
            'timeout': self.timeout, 'stop_on_fail': self.stop_on_fail,
            'last_exit_code': self.last_exit_code,
            'last_output': self.last_output,
        }

    @staticmethod
    def from_dict(d: dict) -> 'Hook':
        return Hook(
            id=d.get('id', ''), name=d.get('name', ''),
            type=d.get('type', 'pre'), command=d.get('command', ''),
            enabled=d.get('enabled', True), timeout=d.get('timeout', 60),
            stop_on_fail=d.get('stop_on_fail', True),
            last_exit_code=d.get('last_exit_code', -1),
            last_output=d.get('last_output', ''),
        )


class HooksManager:
    """Загрузка/сохранение хуков."""

    @staticmethod
    def load() -> List[Hook]:
        try:
            data = json.load(open(HOOKS_FILE, encoding='utf-8'))
            return [Hook.from_dict(d) for d in data]
        except Exception:
            return []

    @staticmethod
    def save(hooks: List[Hook]):
        try:
            json.dump(
                [h.to_dict() for h in hooks],
                open(HOOKS_FILE, 'w', encoding='utf-8'),
                ensure_ascii=False, indent=4
            )
        except Exception as e:
            print(f"[hooks] save failed: {e}")

    @staticmethod
    def new_id() -> str:
        import uuid
        return str(uuid.uuid4())[:8]

    @staticmethod
    def run_hooks(
        hooks: List[Hook],
        hook_type: str,               # 'pre' | 'post'
        cwd: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        Запускает все включённые хуки заданного типа.
        Возвращает True если все прошли успешно (или stop_on_fail=False).
        """
        active = [h for h in hooks if h.enabled and h.type == hook_type]
        if not active:
            return True

        def log(msg, level='info'):
            if callback:
                callback(msg, level)

        log(f"Running {len(active)} {hook_type}-deploy hook(s)...")

        all_ok = True
        for hook in active:
            log(f"  [{hook_type.upper()}] {hook.name}: {hook.command}")
            try:
                result = subprocess.run(
                    hook.command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=hook.timeout,
                    encoding='utf-8',
                    errors='replace'
                )
                hook.last_exit_code = result.returncode
                hook.last_output = (result.stdout + result.stderr).strip()[-500:]

                if result.stdout.strip():
                    for line in result.stdout.strip().splitlines():
                        log(f"    {line}")

                if result.returncode == 0:
                    log(f"  OK: {hook.name} (exit 0)", 'success')
                else:
                    log(f"  FAILED: {hook.name} (exit {result.returncode})", 'error')
                    if result.stderr.strip():
                        for line in result.stderr.strip().splitlines()[-5:]:
                            log(f"    {line}", 'error')
                    if hook.stop_on_fail:
                        all_ok = False
                        log(f"  Stopping: hook '{hook.name}' failed with stop_on_fail=True", 'error')
                        break

            except subprocess.TimeoutExpired:
                hook.last_exit_code = -1
                hook.last_output = f'Timeout after {hook.timeout}s'
                log(f"  TIMEOUT: {hook.name} (>{hook.timeout}s)", 'error')
                if hook.stop_on_fail:
                    all_ok = False
                    break
            except Exception as e:
                hook.last_exit_code = -1
                hook.last_output = str(e)
                log(f"  ERROR: {hook.name}: {e}", 'error')
                if hook.stop_on_fail:
                    all_ok = False
                    break

        # Сохраняем результаты
        HooksManager.save(hooks)
        return all_ok
