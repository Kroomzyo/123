
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# URL внешнего API, к которому мы будем обращаться
backOffice_bets_api = "https://backoffice.pbsvc.bz/api/backoffice/client/information"


@app.route('/get_verificationStatus/', methods=['POST']) #API для получения статуса верификации

def get_data():
    try:
        request_data = {"clientId": request.json["clientId"],
                        "chatId": request.json["chatId"]}

        url = "https://backoffice.pbsvc.bz/api/paygate/client/lastTransactions"
        params = {
            "fsid": "l1I9wLGY9Sfzj7x5bhpZCwY3",
            "userId": "5611",
            "userLang": "ru",
            "clientId": request.json["clientId"],
            "maxCount": 200,
            "login": "nimakarov"
        }

        response = requests.post(url=url, json=params)

        # Чекаем распонс-код
        if response.status_code == 200:
            data = response.json()

            max_lastupdated = 0
            withdrawal_element = None

            for element in data["response"]:
                if element["type"] == "withdrawal" and element["status"] != "SUCCESS" and int(
                        element["createdAt"]) > max_lastupdated:
                    max_lastupdated = int(element["createdAt"])
                    withdrawal_element = element

            if withdrawal_element is not None:
                withdrawal_id = withdrawal_element["id"]
                print(withdrawal_id)
                url = "https://backoffice.pbsvc.bz/api/payoutrisk/getPayoutHistory"
                params = {
                    "clientId": request.json["clientId"],
                    "globalId": f"{withdrawal_id}",
                    "login": "usrPariBackofficeApi",
                    "fsid": "l1I9wLGY9Sfzj7x5bhpZCwY3",
                    "userId": "5611",
                    "userLang": "ru"
                }
                response = requests.post(url=url, json=params)
                data = response.json()
                if data["response"]["list"]:
                    ovv_found = False
                    af_found = False
                    for item in data["response"]["list"]:
                        if "#ОВВ" in item["object"]["userComment"]:
                            ovv_found = True
                        if "#АФ" in item["object"]["userComment"]:
                            af_found = True
                    if ovv_found:
                        result_item = "Требуется ОВВ"
                    elif af_found:
                        result_item = "В обработке АФ"
                    else:
                        result_item = "Недостаточно информации"
                else:
                    result_item = "Верификация не требуется"

            else:
                result_item = "Операция завершена / Недостаточно информации"

            print(result_item)



            result = {'Verification status': f'{result_item}', "clientId": request.json["clientId"]}
            return jsonify(result)
        else:
            #Или возвращаем сообщение об ошибке
            return jsonify({'error': 'Не удалось сфетчить данные'}), 500
    except Exception as e:
        # Возвр саму ошибку
        return jsonify({'error': str(e)}), 500


@app.route('/get_wagersum/', methods=['POST']) #API для получения Суммы отыгрыша бонуса
def get_wager():
    try:
        request_data = {"clientId": request.json["clientId"],
                        "chatId": request.json["chatId"]}
        url = 'https://backoffice.pbsvc.bz/api/backoffice/client/lastOperations'
        data = {
            "clientId": f"{request.json['clientId']}",
            "maxCount": 50000,
            "login": "aagryzkov",
            "fsid": "l1I9wLGY9Sfzj7x5bhpZCwY3",
            "userId": "5611",
            "userLang": "ru"
        }

        response = requests.post(url=url, json=data)
        parsed_data = response.json()
        earliest_allowed_time = 1668805200000    #19.11.2022
        if response.status_code == 200:
            # Находим последние 20 пополнений по времени и ранний депозит
            last_deposits = sorted((operation for operation in parsed_data["response"]["list"] if
                                    operation["object"]["operationKind"] == "69"), key=lambda x: x["object"]["time"],
                                   reverse=True)[:20]
            earliest_deposit_time = last_deposits[-1]["object"]["time"] if last_deposits else 0
            # 19.11.2022
            if earliest_deposit_time >= earliest_allowed_time:
                last_deposits = sorted(
                    (operation for operation in parsed_data["response"]["list"] if
                     operation["object"]["operationKind"] == "69"),
                    key=lambda x: x["object"]["time"], reverse=True)[:20]
                bet_sum = sum(abs(float(operation["object"]["sum"])) for operation in parsed_data["response"]["list"] if
                              operation["object"]["operationKind"] in ["1", "640"] and operation["object"][
                                  "time"] > earliest_deposit_time)


                deposit_sum = abs(sum(float(operation["object"]["sum"]) for operation in last_deposits))

            else:
                last_deposits = sorted((operation for operation in parsed_data["response"]["list"] if
                                        operation["object"]["operationKind"] == "69" and operation["object"][
                                            "time"] >= earliest_allowed_time), key=lambda x: x["object"]["time"],
                                       reverse=True)[:20]

                earliest_deposit_time = last_deposits[-1]["object"]["time"] if last_deposits else 0
                bet_sum = sum(abs(float(operation["object"]["sum"])) for operation in parsed_data["response"]["list"] if
                              operation["object"]["operationKind"] in ["1", "640"] and operation["object"][
                                  "time"] > earliest_deposit_time)
                deposit_sum = abs(sum(float(operation["object"]["sum"]) for operation in last_deposits))

            if bet_sum >= deposit_sum:
                result_item = False
                wagersum = 0
            else:
                result_item = True
                wagersum = round((deposit_sum - bet_sum) / 100)



            result = {'Total_sum': wagersum, 'Status_wager': result_item, 'requestId': request.json["clientId"] }
            return jsonify(result)

        else:
            print(f'Ошибка при выполнении запроса: {response.status_code}')


    except Exception as e:
        # Возвр саму ошибку
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run()
