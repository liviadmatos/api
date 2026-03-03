from flask import Flask, render_template, request, flash, redirect
import requests

app = Flask(__name__)
app.secret_key = "nasa_secret"

API_KEY = "DEMO_KEY" 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/espaco', methods=['POST'])
def buscar_asteroides():
    data_inicio = request.form.get('data_inicio')
    data_fim = request.form.get('data_fim')
    
    if not data_inicio or not data_fim:
        flash("Selecione as duas datas!")
        return redirect('/')

    parametros = {
        'start_date': data_inicio,
        'end_date': data_fim,
        'api_key': API_KEY
    }

    response = requests.get("https://api.nasa.gov/neo/rest/v1/feed", params=parametros)
    dados = response.json()

    if 'near_earth_objects' in dados:
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
        flash("Erro na busca! Lembre-se: o intervalo máximo é de 7 dias.")
        return redirect('/')
    

if __name__ == "__main__":
    app.run(debug=True)