#!/bin/zsh
redis-server & celery -A cubeclash worker -l INFO