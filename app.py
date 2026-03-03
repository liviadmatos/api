from flask import Flask, render_template, request, flash, redirect
import requests

app = Flask(__name__)
app.secret_key = "nasa_secret"

API_KEY = "DEMO_KEY" 

@app.route('/')
def index():
    # se vierem como args (após redirecionamentos), reusa para preencher o formulário
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    return render_template('index.html', data_inicio=data_inicio, data_fim=data_fim)

@app.route('/espaco', methods=['POST'])
def buscar_asteroides():
    data_inicio = request.form.get('data_inicio')
    data_fim = request.form.get('data_fim')
    
    if not data_inicio or not data_fim:
        flash("Selecione as duas datas!")
        # redirecionar mantendo valores já preenchidos (se houver)
        return redirect(f"/?data_inicio={data_inicio or ''}&data_fim={data_fim or ''}")

    parametros = {
        'start_date': data_inicio,
        'end_date': data_fim,
        'api_key': API_KEY
    }

    try:
        # definir timeout para evitar esperas indefinidas
        response = requests.get(
            "https://api.nasa.gov/neo/rest/v1/feed",
            params=parametros,
            timeout=10
        )
        response.raise_for_status()  # levanta exceções para códigos 4xx/5xx

        dados = response.json()  # pode levantar ValueError

    except requests.exceptions.Timeout:
        flash("Tempo de conexão esgotado. Verifique sua internet e tente novamente.")
        return redirect(f"/?data_inicio={data_inicio}&data_fim={data_fim}")
    except requests.exceptions.ConnectionError:
        flash("Não foi possível conectar à API da NASA. Verifique sua conexão de rede.")
        return redirect(f"/?data_inicio={data_inicio}&data_fim={data_fim}")
    except requests.exceptions.HTTPError as err:
        status = err.response.status_code if err.response is not None else '??'
        reason = err.response.reason if err.response is not None else ''
        flash(f"A requisição retornou um erro HTTP {status} {reason}.")
        return redirect(f"/?data_inicio={data_inicio}&data_fim={data_fim}")
    except ValueError:
        flash("Resposta da API não pôde ser interpretada. Acesso ou formato inesperado.")
        return redirect(f"/?data_inicio={data_inicio}&data_fim={data_fim}")
    except Exception as err:
        flash(f"Erro inesperado: {err}")
        return redirect(f"/?data_inicio={data_inicio}&data_fim={data_fim}")

    # se a requisição foi bem-sucedida, conferir dados esperados
    if isinstance(dados, dict) and 'near_earth_objects' in dados:
        # A API traz os dados agrupados por data. 
        # Vamos "desmanchar" as datas e colocar todos os asteroides em uma lista só.
        objetos_por_data = dados['near_earth_objects']
        lista_final = []

        for data in objetos_por_data:
            for asteroide in objetos_por_data[data]:
                info = {
                    "data_passagem": data,
                    "nome": asteroide['name'],
                    "perigoso": asteroide['is_potentially_hazardous_asteroid'],
                    "tamanho_max": round(asteroide['estimated_diameter']['meters']['estimated_diameter_max'], 2),
                    "velocidade": round(float(asteroide['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']), 2),
                    "distancia": round(float(asteroide['close_approach_data'][0]['miss_distance']['kilometers']), 2)
                }
                lista_final.append(info)
        
        # Ordenar por data para não ficar "nada a ver"
        lista_final = sorted(lista_final, key=lambda x: x['data_passagem'])

        return render_template('espaco.html', asteroides=lista_final, inicio=data_inicio, fim=data_fim)
    else:
        # caso a API tenha retornado outra estrutura (por exemplo, intervalo > 7 dias)
        flash("Erro na busca! Lembre-se: o intervalo máximo é de 7 dias.")
        return redirect(f"/?data_inicio={data_inicio}&data_fim={data_fim}")
    

if __name__ == "__main__":
    app.run(debug=True)