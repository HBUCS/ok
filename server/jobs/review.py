from server.models import Backup, ReviewSetting
from server import jobs
from server.review import cleanup_tempfiles
from server.review.clang import Clang
from server.review.flake8 import Flake8


tools = {"flake8": Flake8,
         "clang": Clang}


@jobs.background_job
def review_code(assign_id=None, backup_id=None):
    logger = jobs.get_job_logger()

    backup = Backup.query.filter_by(id=backup_id).one_or_none()
    if not backup:
        logger.info("Could not find backup")
        return
    settings = ReviewSetting.query.filter_by(assignment_id=assign_id,
                                             enable=True)

    for item in settings:
        tool = tools[item.kind](backup, settings=item.content)
        tool.handle_files()

    cleanup_tempfiles()
