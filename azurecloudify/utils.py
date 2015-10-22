import random
import string
from cloudify import ctx

def random_suffix_generator(size=5, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# Clean runtime_properties
def clear_runtime_properties():
    for key in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties[key] = None


def request_failed(caller_string, raw_response):
    ctx.logger.info("In request_failed:{}".format(caller_string))
    response_get_info = raw_response.json()
    error_keys = ('error', u'error')
    code_keys = ('code', u'code')
    message_keys = ('message', u'message')
    for curr_error_key in error_keys:
        if curr_error_key in response_get_info:
            ctx.logger.info("Error occurred in {}".format(caller_string))
            curr_error = response_get_info[curr_error_key]
            for curr_code_key in code_keys:
                if curr_code_key in curr_error:
                    curr_code_value = curr_error[curr_code_key]
                    ctx.logger.info("Error code is {} in {}".format(curr_code_value,caller_string))
                    for curr_message_key in message_keys:
                        if curr_message_key in curr_error:
                            curr_message_value = curr_error[curr_message_key]
                            ctx.logger.info("Error message is {} in {}".format(curr_message_value,caller_string))
                            return True
                    return True
            return True

    return False
