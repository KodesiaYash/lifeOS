#!/usr/bin/env sh
set -eu

exec arq src.scheduling.worker.WorkerSettings
