#!/bin/bash

# shellcheck disable=SC2164
cd ~/tg-bot
#cd /Users/evgenybondarik/Downloads/botly/tg-bot

git checkout master
git pull

# Получите аргументы командной строки
TG_TOKEN=$1
TG_OWNER_CHAT_ID=$2
TG_BOT_NAME=$3
TG_BOT_ID=$4
TG_BOT_OWNER_USER_ID=$5
FIREBASE_TOKEN=$6
FIREBASE_PROJECT=$7

# Установите конфигурацию firebase
firebase --project=${FIREBASE_PROJECT} --token ${FIREBASE_TOKEN} functions:config:set telegram.token="${TG_TOKEN}"
firebase --project=${FIREBASE_PROJECT} --token ${FIREBASE_TOKEN} functions:config:set telegram.owner_chat_id="${TG_OWNER_CHAT_ID}"
firebase --project=${FIREBASE_PROJECT} --token ${FIREBASE_TOKEN} functions:config:set telegram.name="${TG_BOT_NAME}"
firebase --project=${FIREBASE_PROJECT} --token ${FIREBASE_TOKEN} functions:config:set telegram.bot_owner_user_id="${TG_BOT_OWNER_USER_ID}"
firebase --project=${FIREBASE_PROJECT} --token ${FIREBASE_TOKEN} functions:config:set telegram.bot_id="${TG_BOT_ID}"

# Получите конфигурацию firebase
firebase functions:config:get > .runtimeconfig.json

# Разверните функции firebase
firebase --project=${FIREBASE_PROJECT} --token ${FIREBASE_TOKEN} deploy --only functions:${TG_BOT_NAME}