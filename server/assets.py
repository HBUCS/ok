from flask_assets import Bundle

landing_css = Bundle(
    'css/landing.css',
    filters='cssmin',
    output='public/css/landing.css'
)

common_css = Bundle(
    'css/helper.css',
    'css/main.css',
    'css/highlight.css',
    'css/code.css',
    'css/swal-theme.css',
    'css/notebook.css',
    'lib/notebookjs/notebook.css',
    filters='cssmin',
    output='public/css/common.css'
)

oauth_css = Bundle(
    'css/oauth.css',
    'css/landing.css',
    filters='cssmin',
    output='public/css/oauth.css'
)

common_js = Bundle(
    'js/main.js',
    'js/notebook.js',
    'lib/notebookjs/notebook.min.js',
    'lib/notebookjs/ansi_up.min.js',
    filters='jsmin',
    output='public/js/common.js'
)

student_css = Bundle(
    'css/student.css',
    filters='cssmin',
    output='public/css/student.css'
)

student_js = Bundle(
    'js/student.js',
    'js/comments.js',
    filters='jsmin',
    output='public/js/student.js'
)

staff_css = Bundle(
    'css/staff.css',
    'css/jquery.steps.css',
    filters='cssmin',
    output='public/css/staff.css'
)

staff_js = Bundle(
    'js/staff.js',
    'js/comments.js',
    'lib/listjs/list.pagination.js',
    'lib/pygal/pygal-tooltips.min.js',
    filters='jsmin',
    output='public/js/staff.js'
)
