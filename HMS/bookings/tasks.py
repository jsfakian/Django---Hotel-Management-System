import logging
import subprocess
import sys
from pathlib import Path

try:
    from celery import shared_task
except ImportError:
    def shared_task(func=None, *args, **kwargs):
        def decorator(inner_func):
            inner_func.delay = inner_func
            return inner_func

        if callable(func):
            return decorator(func)
        return decorator


logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK3_ALGORITHMS_DIR = REPO_ROOT / 'task3-algorithms'


def _run_training_script(script_name):
    script_path = TASK3_ALGORITHMS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f'Task3 script not found: {script_path}')

    process = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(TASK3_ALGORITHMS_DIR),
        capture_output=True,
        text=True,
        check=False,
    )

    result = {
        'script': script_name,
        'returncode': process.returncode,
        'stdout_tail': '\n'.join(process.stdout.splitlines()[-20:]),
        'stderr_tail': '\n'.join(process.stderr.splitlines()[-20:]),
    }

    if process.returncode != 0:
        logger.error('Task3 script failed: %s', result)
        raise RuntimeError(f'{script_name} failed with code {process.returncode}')

    logger.info('Task3 script completed successfully: %s', script_name)
    return result


@shared_task
def train_task3_models():
    """Run the complete Task3 training pipeline."""
    return _run_training_script('train_all.py')


@shared_task
def train_task3_pricing_model():
    """Run Task3 pricing model training."""
    return _run_training_script('train_pricing.py')


@shared_task
def train_task3_forecasting_model():
    """Run Task3 forecasting model training."""
    return _run_training_script('train_forecasting.py')


@shared_task
def train_task3_recommendation_model():
    """Run Task3 recommendation model training."""
    return _run_training_script('train_recommendations.py')
