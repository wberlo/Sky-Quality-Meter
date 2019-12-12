MQTT version of the sky quality meter.
Uses two pulish topics:
topic_pub = b'SQM'
topic_pub_time = b'Date'

One subscribe topic, just in case the sqm should receive something
topic_sub = b'notification'
