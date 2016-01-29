"""
User logout
"""
from base_common.dbatokens import authorized_by_token
from base_common.dbatokens import close_session_by_token
import base_common.msg
from base_lookup import api_messages as msgs
from base_common.dbacommon import get_md2db
from base_common.dbacommon import app_api_method


name = "Logout"
location = "user/logout"
request_timeout = 10


@app_api_method
def do_post(request, *args, **kwargs):
    """
    User logout
    :param Auth: authorization token in header, string, True
    :return:  200, OK
    :return:  400
    """

    log = request.log

    _db = get_md2db()
    dbc = _db.cursor()

    tk = request.auth_token
    if not authorized_by_token(dbc, tk, log):
        return base_common.msg.error(msgs.UNAUTHORIZED_REQUEST)

    if not close_session_by_token(dbc, tk, log):
        log.warning("Clossing session with token {}".format(tk))
        return base_common.msg.error(msgs.CLOSE_USER_SESSION)

    _db.commit()

    return base_common.msg.post_ok()
