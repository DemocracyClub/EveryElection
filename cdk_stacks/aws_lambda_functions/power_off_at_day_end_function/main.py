from power_off_helper import reduce_alb_size


def handler(event, context):
    tag_name = event["tag_name"]
    tag_value = event["tag_value"]
    at_most = event["at_most"]

    reduce_alb_size(tag_name=tag_name, tag_value=tag_value, at_most=at_most)
