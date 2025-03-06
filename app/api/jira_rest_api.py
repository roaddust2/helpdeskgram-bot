import io
import aiohttp
from settings import JIRA_HOME, JIRA_USERNAME, JIRA_PASSWORD
import logging


SESSION_COOKIE = None


class JiraFailure(Exception):

    def __init__(self):
        self.message = "Something went wrong with Jira integration!"

    def __str__(self):
        return self.message


async def get_jira_cookie():
    """Function that retrieves JSESSIONID cookie"""

    global SESSION_COOKIE

    url = f"{JIRA_HOME}/rest/auth/1/session"
    headers = {"Content-Type": "application/json"}
    json = {
        "username": JIRA_USERNAME,
        "password": JIRA_PASSWORD
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json=json
        ) as response:
            if response.status == 200:
                data = await response.json()
                SESSION_COOKIE = data.get('session')
                return data
            else:
                logging.error(f"Failed to get cookie, {response.status} {response.text}")
                return None


async def create_jira_issue(issue_data: dict):
    """Function that creates a Jira issue using JSESSIONID cookie"""

    global SESSION_COOKIE

    url = f"{JIRA_HOME}/rest/api/2/issue"
    headers = {'Content-Type': 'application/json'}

    if not SESSION_COOKIE:
        logging.info("Session cookie is not set. Trying to authenticate...")
        await get_jira_cookie()

    if SESSION_COOKIE:
        headers.update({'Cookie': f"{SESSION_COOKIE['name']}={SESSION_COOKIE['value']}"})
    else:
        logging.error("Authentication failed.")
        return None

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json={"fields": issue_data}
        ) as response:
            if response.status == 201:
                data = await response.json()
                logging.info(f"Issue created with key {data['key']}.")
                return data['key']
            elif response.status == 401:
                logging.error("Unauthorized. Retry...")
                return await create_jira_issue(issue_data)
            elif response.status == 400:
                logging.error(f"Input is invalid! {response.status} {await response.text()}")
            else:
                logging.error(f"Failed to create issue! {response.status} {await response.text()}")
                raise JiraFailure


# TODO: Needs refactoring
async def upload_jira_issue_attachments(
    issue_key: str,
    attachments: list[tuple[io.BytesIO, str]],
    retries=3
):
    """Function that uploads attachments to specified Jira issue"""

    global SESSION_COOKIE

    url = f"{JIRA_HOME}/rest/api/2/issue/{issue_key}/attachments"
    headers = {'X-Atlassian-Token': 'no-check'}

    if not SESSION_COOKIE:
        logging.info("Session cookie is not set. Trying to authenticate...")
        await get_jira_cookie()

    if SESSION_COOKIE:
        headers.update({'Cookie': f"{SESSION_COOKIE['name']}={SESSION_COOKIE['value']}"})
    else:
        logging.error("Authentication failed.")
        return None

    for attempt in range(retries):
        async with aiohttp.ClientSession() as session:

            # About multiform and name "file"
            # https://docs.atlassian.com/software/jira/docs/api/REST/9.12.9/#api/2/issue/{issueIdOrKey}/attachments-addAttachment

            form = aiohttp.FormData()

            for file_bytes, filename in attachments:
                file_bytes.seek(0)
                form.add_field(
                    "file",  # This "file" name
                    file_bytes,
                    filename=filename
                )

            async with session.post(
                url=url,
                headers=headers,
                data=form
            ) as response:
                if response.status == 200:
                    logging.info("Image/s successfully updated.")
                    return await response.json()
                elif response.status == 401:
                    logging.info(f"Session expired. Refreshing session... (Attempt {attempt + 1}/{retries})")
                    await get_jira_cookie()
                    if SESSION_COOKIE:
                        headers.update({'Cookie': f"{SESSION_COOKIE['name']}={SESSION_COOKIE['value']}"})
                    else:
                        logging.error("Failed to refresh session.")
                        return None
                elif response.status == 403:
                    logging.error("Attachments are disabled or you don't have permission to add attachments to this issue.")
                    return None
                elif response.status == 404:
                    logging.error(f"Issue is not found, the user does not have permission to view it, or the attachments exceeds the max size.\n{await response.text()}")
                    return None
                else:
                    logging.error(f"Failed to upload attachment! {response.status} {await response.text()}")
                    raise JiraFailure
    raise JiraFailure


async def get_jira_issue_last_comment(issue_key: str) -> str:
    """Function that gets last issue comment by issue key"""

    global SESSION_COOKIE

    url = f"{JIRA_HOME}/rest/api/2/issue/{issue_key}/comment"
    headers = dict()

    if not SESSION_COOKIE:
        logging.info("Session cookie is not set. Trying to authenticate...")
        await get_jira_cookie()

    if SESSION_COOKIE:
        headers.update({'Cookie': f"{SESSION_COOKIE['name']}={SESSION_COOKIE['value']}"})
    else:
        logging.error("Authentication failed.")
        return None
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data["comments"]:
                    last_comment = max(data["comments"], key=lambda c: c["created"])["body"]
                    logging.info(f"Get comments for {issue_key}.")
                    return last_comment
                else:
                    logging.info(f"No comments for {issue_key}.")
                    return None
            elif response.status == 404:
                logging.error("Issue key does not have exist or you don'thave permission to view issue")
                return None
            else:
                logging.error(f"Failed to get comments {response.status} {await response.text()}")
                raise JiraFailure
