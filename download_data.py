"""
Automated FracFocus Data Downloader

Downloads the latest FracFocus CSV data from the official source.
Can be run manually or scheduled via cron/Task Scheduler.
"""

import requests
import os
from pathlib import Path
from datetime import datetime
import logging
import sys

# Setup logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'download_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
FRACFOCUS_URL = 'https://www.fracfocusdata.org/digitaldownload/FracFocusCSV.zip'
DATA_DIR = Path('data')
DOWNLOAD_PATH = DATA_DIR / 'fracfocus_data.zip'
BACKUP_DIR = DATA_DIR / 'backups'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)


def download_data(url: str, output_path: Path, timeout: int = 600) -> bool:
    """
    Download FracFocus data from the official source.

    Args:
        url: Download URL
        output_path: Where to save the ZIP file
        timeout: Download timeout in seconds (default: 10 minutes)

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting download from {url}")
    logger.info(f"Output path: {output_path}")

    try:
        # Stream download for large files
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        if total_size:
            logger.info(f"File size: {total_size / (1024*1024):.2f} MB")

        # Download with progress tracking
        downloaded = 0
        chunk_size = 8192

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Log progress every 50 MB
                    if downloaded % (50 * 1024 * 1024) < chunk_size:
                        if total_size:
                            pct = (downloaded / total_size) * 100
                            logger.info(f"Progress: {downloaded / (1024*1024):.2f} MB ({pct:.1f}%)")
                        else:
                            logger.info(f"Progress: {downloaded / (1024*1024):.2f} MB")

        logger.info(f"Download complete: {downloaded / (1024*1024):.2f} MB")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        return False


def backup_existing_data(current_path: Path, backup_dir: Path) -> None:
    """
    Backup existing data file before replacing it.

    Args:
        current_path: Path to current data file
        backup_dir: Directory to store backups
    """
    if current_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'fracfocus_data_{timestamp}.zip'

        logger.info(f"Backing up existing data to {backup_path}")

        try:
            import shutil
            shutil.copy2(current_path, backup_path)
            logger.info("Backup complete")

            # Clean up old backups (keep last 5)
            backups = sorted(backup_dir.glob('fracfocus_data_*.zip'))
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    logger.info(f"Removing old backup: {old_backup.name}")
                    old_backup.unlink()

        except Exception as e:
            logger.warning(f"Backup failed (continuing anyway): {e}")


def check_if_update_needed(current_path: Path) -> bool:
    """
    Check if we should download new data.

    Simple check: if file is older than 1 day, download new version.
    FracFocus updates 5 days/week, so daily checks ensure we stay current.

    Args:
        current_path: Path to current data file

    Returns:
        True if update needed, False otherwise
    """
    if not current_path.exists():
        logger.info("No existing data file found - download needed")
        return True

    # Check file age
    file_age_seconds = datetime.now().timestamp() - current_path.stat().st_mtime
    file_age_days = file_age_seconds / (24 * 3600)

    logger.info(f"Current data file age: {file_age_days:.2f} days")

    if file_age_days > 1:
        logger.info("Data is older than 1 day - download needed")
        return True
    else:
        logger.info("Data is recent - skipping download")
        return False


def main(force: bool = False):
    """
    Main execution function.

    Args:
        force: If True, download regardless of file age
    """
    logger.info("=" * 60)
    logger.info("FracFocus Data Downloader")
    logger.info("=" * 60)

    # Check if update is needed (unless forced)
    if not force and not check_if_update_needed(DOWNLOAD_PATH):
        logger.info("No update needed - exiting")
        return 0

    # Backup existing data
    backup_existing_data(DOWNLOAD_PATH, BACKUP_DIR)

    # Download new data
    success = download_data(FRACFOCUS_URL, DOWNLOAD_PATH)

    if success:
        logger.info("✓ Data download successful")
        logger.info(f"File saved to: {DOWNLOAD_PATH.absolute()}")

        # Remove old consolidated data (will be regenerated on next analysis)
        consolidated_path = DATA_DIR / 'consolidated_data.csv'
        if consolidated_path.exists():
            logger.info("Removing old consolidated data (will be regenerated)")
            consolidated_path.unlink()

        logger.info("\nNext steps:")
        logger.info("  1. Run: python fracfocus_analysis.py")
        logger.info("  2. Run: python dashboard.py")

        return 0
    else:
        logger.error("✗ Data download failed")
        return 1


if __name__ == '__main__':
    # Check for --force flag
    force = '--force' in sys.argv

    if force:
        logger.info("Force download mode enabled")

    exit_code = main(force=force)
    sys.exit(exit_code)
