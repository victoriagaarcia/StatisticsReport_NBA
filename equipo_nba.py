# Importamos las librerías necesarias
from bs4 import BeautifulSoup
from fpdf import FPDF
import pandas as pd
import requests
import re

def extract_webscraping(predictions_url):
    # Sacamos la información que necesitamos de la web de pronósticos especificada
    info = requests.get(predictions_url)
    soup = BeautifulSoup(info.content, 'html.parser') # 'html.parser' indica que trabajamos con una web escrita en html
    # Obtenemos una lista con el código html referente a cada partido recogido en la web de pronósticos
    matches = soup.find_all('div', {'class': 'cursor-pointer border rounded-md mb-4 px-1 py-2 flex flex-col lg:flex-row relative'})
    return matches

def transform_webscraping(team, matches):
    team_predictions = []
    for match in matches:
        # Obtenemos el nombre del partido con el código referente a la subclase del partido ('span')
        match_title = match.find('span', {'class': 'font-medium w-full lg:w-1/2 text-center dark:text-white'}).text[2:-2]
        # Guardamos los nombres de los dos partidos participantes y limpiamos los caracteres innecesarios (saltos de línea)
        match_teams = match_title.split(' - ')
        for position in range(2): match_teams[position] = re.sub('\W\s', '', match_teams[position])
        # Si el equipo que estamos analizando participa en el partido, continuamos extrayendo los detalles del partido
        if team in match_teams:
            # Podemos obtener la fecha y hora del partido en cuestión
            match_when = match.find('span', {'class': 'text-sm text-gray-600 w-full lg:w-1/2 text-center dark:text-white'}).text
            match_date = match_when.split(' - ')[0]
            match_time = match_when.split(' - ')[1]
            # Extraemos las cuotas correspondientes con cada equipo del partido
            match_odds = match.find_all('span', {'class': 'px-1 h-booklogosm font-bold bg-primary-yellow text-white leading-8 rounded-r-md w-14 md:w-18 flex justify-center items-center text-base'})
            for position in range(2): match_odds[position] = match_odds[position].text
            # El ganador será el que tenga menor valor de cuota (significa que su probabilidad de ganar es mayor)
            winner = match_teams[match_odds.index(min(match_odds))]
            # Construimos un diccionario con los datos del partido
            keys = ['Match Title', 'Date', 'Time', 'Team 1', 'Odds 1', 'Team 2', 'Odds 2', 'Winner']
            values = [match_title, match_date, match_time, match_teams[0], match_odds[0], match_teams[1], match_odds[1], winner]
            dict_info = {}
            for number in range(8): dict_info[keys[number]] = values[number]
            # Añadimos el diccionario a la lista, para tener finalmente una lista con cada partido desglosado en forma de diccionario
            team_predictions.append(dict_info)
    return team_predictions

def load_webscraping(team_predictions, team):
    print(f'Los pronósticos para los próximos partidos del equipo {team} son:')
    for match in team_predictions:
        # Mostramos por pantalla los pronósticos de cada partido del equipo seleccionado
        print('\n')
        print(f"En el partido {match['Match Title']} que se jugará el {match['Date']} a las {match['Time']}, ganará el equipo {match['Winner']}.")
        print(f"La cuota de {match['Team 1']} es {match['Odds 1']} y la de {match['Team 2']} es {match['Odds 2']}; por lo que {match['Winner']} tendrá mayor probabilidad de ganar.")
    
def extract_api(endpoint, head):
    # Extraemos la información de la API con el endpoint especificado y las cabeceras
    response = requests.get(endpoint, headers = head)
    # Convertimos los datos en una lista de diccionarios
    dict_content = response.json()
    # Pasamos los datos a un dataframe
    nba_info = pd.DataFrame(dict_content)
    return nba_info

def transform_api(nba_info):
    # Creamos un dataframe vacío para incluir las categorías relativas a los jugadores
    players = pd.DataFrame()
    # La primera columna incluirá el nombre del jugador y su posición en el campo
    players['Player (Position)'] = nba_info["Name"] + ' (' + nba_info["Position"] + ')'
    # Se añaden las demás columnas relevantes al dataframe de jugadores
    players_columns = ['G', 'Min', 'Pts', 'OR', 'DR', 'Reb', 'A', 'Stl', 'Blk', 'TO', 'PF', 'USR', '+/-']
    players_info = ['Games', 'Minutes', 'Points', 'OffensiveRebounds', 'DefensiveRebounds', 'Rebounds', 'Assists', 'Steals', 'BlockedShots', 'Turnovers', 'PersonalFouls', 'UsageRatePercentage', 'PlusMinus']
    for column in range(13): # El dataframe de jugadores tendrá 14 columnas en total (contando con la primera)
        players[players_columns[column]] = nba_info[players_info[column]]
    
    # Creamos un dataframe vacío para incluir las categorías relativas a los tiros
    shots = pd.DataFrame()
    # La primera columna incluirá el nombre del jugador y su posición en el campo
    shots['Player (Position)'] = nba_info["Name"] + ' (' + nba_info["Position"] + ')'
    # Se añaden las demás columnas relevantes al dataframe de tiros
    shots_columns = ['FGM', 'FGA', 'FG%', '3PM', '3PA', '3P%', '2PM', '2PA', '2P%', 'FTM', 'FTA', 'FT%', 'PER']
    shots_info = ['FieldGoalsMade', 'FieldGoalsAttempted', 'FieldGoalsPercentage', 'ThreePointersMade', 'ThreePointersAttempted', 'ThreePointersPercentage', 'TwoPointersMade', 'TwoPointersAttempted', 'TwoPointersPercentage', 'FreeThrowsMade', 'FreeThrowsAttempted', 'FreeThrowsPercentage', 'PlayerEfficiencyRating']
    for column in range(13): # El dataframe de tiros tendrá 14 columnas en total (contando con la primera)
        shots[shots_columns[column]] = nba_info[shots_info[column]]
    return players, shots

def load_api(players, shots):
    # Creamos el PDF en el que adjuntaremos el informe, en tamaño A4 y con coordenadas en milímetros
    # La orientación es horizontal ('L') para que se lea correctamente la información de las tablas
    pdf = PDF('L', 'mm', 'A4')
    # Establecemos los márgenes del documento
    pdf.set_margins(23, 25, 23)
    pdf.set_auto_page_break(auto = True, margin = 26)
    # Contamos las páginas del documento a medida que se crean
    pdf.alias_nb_pages()
    # Especificamos el autor del documento
    pdf.set_author('Victoria García M-E')

    # Creamos la portada del informe llamando a la función creada
    pdf.cover()

    # Creamos la página con la introducción llamando a la función creada
    pdf.add_page()
    pdf.intro()

    # Creamos una página con la tabla a nivel de jugador
    pdf.add_page()
    pdf.set_y(17)
    # Establecemos un título
    pdf.set_text_color(0, 117, 139)
    pdf.set_font('times', 'B', 13)
    pdf.cell(0, 10, 'Estadísticas por jugador - Temporada 22/23', align = 'C')
    pdf.ln(18)
    # Incluimos un párrafo explicativo
    pdf.set_text_color(0)
    pdf.set_font('times', '', 11)
    text_players = 'En esta tabla se muestran los datos por cada jugador de las categorías indicadas. Tal y como se ha resaltado al comienzo, los valores decimales (que no sean porcentajes) hacen referencia al promedio del jugador en la categoría en cuestión. La última columna (+/-) indica la media de puntos marcados cuando el jugador correspondiente se encuentra en el terreno de juego. Para saber el significado de las abreviaturas y siglas de cada columna, ver en la página 2 las explicaciones en la parte inferior izquierda.'
    pdf.multi_cell(246, 5.5, text_players, align = 'J')
    pdf.ln(7)
    # Adjuntamos la tabla correspondiente llamando a la función creada con el dataframe de jugadores
    pdf.draw_table(players)

    # Creamos una página con la tabla a nivel de tiros
    pdf.add_page()
    pdf.set_y(17)
    # Establecemos un título
    pdf.set_text_color(0, 117, 139)
    pdf.set_font('times', 'B', 13)
    pdf.cell(0, 10, 'Estadísticas por tiros - Temporada 22/23', align = 'C')
    pdf.ln(18)
    # Incluimos un párrafo explicativo
    pdf.set_text_color(0)
    pdf.set_font('times', '', 11)
    text_shots = 'En esta tabla se muestran los datos de cada jugador por tipo de tiro en las categorías indicadas. Tal y como se ha resaltado al comienzo, los valores decimales (que no sean porcentajes) hacen referencia al promedio del jugador en la categoría en cuestión. La última columna (PER) indica el porcentaje de eficiencia global del jugador correspondiente, en base a ciertos parámetros. Para saber el significado de las abreviaturas y siglas de cada columna, ver en la página 2 las explicaciones en la parte inferior derecha.'
    pdf.multi_cell(246, 5.5, text_shots, align = 'J')
    pdf.ln(7)
    # Adjuntamos la tabla correspondiente llamando a la función creada con el datagrame de tiros
    pdf.draw_table(shots)

    # Creamos una página explicando las posiciones del baloncesto llamando a la función creada
    pdf.add_page()
    pdf.positions()

    # Creamos una página adjuntando la plantilla del equipo llamando a la función creada
    pdf.add_page()
    pdf.roster()

    # Exportamos el documento en formato PDF
    pdf.output('Stats_Report_NBA.pdf')

class PDF(FPDF):
    def cover(self): # Esta función crea la portada del documento
        self.add_page()
        # Escribimos el título del documento
        self.set_text_color(32, 21, 70)
        self.set_font('times', 'B', 36)
        self.set_y(30)
        self.cell(0, 15, 'CHARLOTTE HORNETS', align = 'C')
        self.ln(15)
        self.set_text_color(0, 117, 139)
        self.set_font_size(28)
        self.cell(0, 12, '2022-2023 Season Statistics Report', align = 'C')
        self.ln(21)
        # Incluimos una imagen con el logo del equipo
        self.image('charlottehornets_logo.png', x = 83, w = 130)
        self.ln(6)
        # Añadimos el nombre y la fuente de los datos
        self.set_text_color(32, 21, 70)
        self.set_font('times', '', 14)
        self.cell(0, 8, 'By Victoria García Martínez-Echevarría', align = 'C')
        self.ln(6)
        self.set_text_color(0, 117, 139)
        self.cell(0, 8, 'Data Source: https://sportsdata.io/developers/api-documentation/nba#', align = 'C')

    def footer(self): # Esta función establece el pie de página
        self.set_y(-20)
        self.set_font('times', '', 11)
        self.set_text_color(120)
        # Incluimos el número de página contando con el total de páginas
        self.cell(0, 10, 'Página ' + str(self.page_no()) + '/{nb}', align = 'C')
    
    def intro(self): # Esta función crea la página introductoria
        self.set_y(17)
        # Establecemos un título
        self.set_text_color(0, 117, 139)
        self.set_font('times', 'B', 13)
        self.cell(0, 10, 'Estadísticas NBA - Charlotte Hornets', align = 'C')
        self.ln(18)

        # Incluimos un párrafo con información general sobre el equipo 
        self.set_text_color(0)
        self.set_font('times', '', 11)
        intro_text = 'En este informe se adjuntan los datos estadísticos más relevantes del equipo Charlotte Hornets de la NBA para la temporada 2022-2023. Este equipo, fundado en 1988, actualmente tiene como entrenador a Steve Clifford y como propietario a Michael Jordan, quien adquirió el equipo en 2010. Los partidos locales se juegan en el Spectrum Center, ubicado en el centro de la ciudad de Charlotte (en Carolina del Norte).\n\nEn este documento se adjuntan dos grandes tablas que resumen de forma visual las estadísticas a nivel de jugador y a nivel de tiros de cada uno de los miembros del equipo. También se adjunta un esquema de las posiciones que se toman en los partidos de este deporte, así como una imagen con los jugadores que conforman la plantilla. En ambas tablas, se encuentra entre paréntesis la posición que ocupa cada jugador justo después de su nombre.\n\nA continuación, se muestra un glosario indicando el significado de las columnas de cada una de las tablas. Cabe resaltar que aquellos datos que sean números decimales hacen referencia a la media por partido de dicha categoría.'
        self.multi_cell(247, 5.5, intro_text, align = 'J')
        self.ln(9)

        # Añadimos el glosario de los nombres de las columnas de ambas tablas
        self.set_font('times', 'B', 11)
        self.cell(123, 6, 'Estadísticas a nivel de jugador')
        self.cell(123, 6, 'Estadísticas a nivel de tiros')
        self.ln(9)
        self.set_font('times', '', 11)
        columns_players = ['G: partidos jugados', 'Min: minutos jugados', 'Pts: media de puntos marcados', 'OR: media de rebotes ofensivos', 'DR: media de rebotes defensivos', 'Reb: media de rebotes totales', 'A: media de asistencias', 'Stl: media de robos de balón', 'Blk: media de bloqueos', 'TO: media de pérdidas de balón', 'PF: media de faltas', 'USR: porcentaje de la tasa de uso', '+/-: Plus/Minus']
        columns_shots = ['FGM: media de tiros de campo marcados', 'FGA: media de tiros de campo intentados', 'FG%: porcentaje de tiros de campo', '3PM: media de tiros de 3 puntos marcados', '3PA: media de tiros de 3 puntos intentados', '3P%: porcenta de tiros de 3 puntos', '2PM: media de tiros de 2 puntos marcados', '2PA: media de tiros de dos puntos intentados', '2P%: porcentaje de tiros de dos puntos', 'FTM: media de tiros libres marcados', 'FTA: media de tiros libres intentados', 'FT%: porcentaje de tiros libres', 'PER: tasa de eficiencia del jugaddor']
        for category in range(13):
            self.cell(125, 6, f' -  {columns_players[category]}')
            self.cell(123, 6, f' -  {columns_shots[category]}')
            self.ln(5.5)

    def draw_table(self, dataframe): # Esta función pinta una tabla con el dataframe que se le pase
        # Las líneas de la tabla serán de color gris
        self.set_draw_color(130)
        available_width = self.w - 90
        columns = list(dataframe.columns)
        # Todas las columnas, exceptuando la del nombre, tendrán la misma anchura
        column_width = available_width / 13
        
        # Escribimos el nombre de cada columna en negrita
        self.set_font('times', 'B', 11)
        self.set_text_color(0)
        self.cell(39, 7, columns[0], 1, align = 'C')
        for column in range(1, len(columns)):
            self.cell(column_width, 7, columns[column], 1, align = 'C')
        self.ln()
        
        # Escribimos la información del dataframe en la tabla
        self.set_font('times', '', 11)
        for row in range(len(dataframe)):
            # El nombre de cada jugador se escribe de color diferente y en una columna más ancha
            self.set_text_color(76, 0, 153)
            self.cell(39, 7, dataframe.loc[row, columns[0]], 1, align = 'C')
            self.set_text_color(0)
            for column in range(1, len(columns)):
                # Para la columna de '+/-' de la primera tabla, se escribirán en rojo los valores negativos y en verde los positivos
                if columns[column] == '+/-':
                    if dataframe.loc[row, columns[column]] > 0:
                        self.set_text_color(0, 153, 76)
                    else:
                        self.set_text_color(204, 0, 0)
                self.cell(column_width, 7, str(dataframe.loc[row, columns[column]]), 1, align = 'C')
                self.set_text_color(0)
            self.ln()
        
    def positions(self): # Esta función crea la página con la explicación de las posiciones
        self.set_y(17)
        # Establecemos un título
        self.set_text_color(0, 117, 139)
        self.set_font('times', 'B', 13)
        self.cell(0, 10, 'Posiciones en baloncesto (Esquema)', align = 'C')
        self.ln(18)

        # Incluimos un párrafo explicativo
        self.set_text_color(0)
        self.set_font('times', '', 11)
        positions_text = 'Se adjunta a continuación un diagrama esquemático mostrando dónde se sitúan en el campo cada una de las posiciones de los jugadores. Aparece una única mitad del campo pero para el equipo contrario las posiciones serían idénticas, en su respectiva mitad. Se incluyen también las traducciones a español de cada título (los datos proporcionados están en inglés y por tanto aparecen en dicho idioma en las tablas anteriores).'
        self.multi_cell(247, 5.5, positions_text, align = 'J')
        self.ln(10)
        # Adjuntamos una imagen con un diagrama de las posiciones
        self.image('basketball_positions.png', x = 29, y = 55, w = 130)

        self.set_y(92)
        # Escribimos las traducciones de las posiciones, numerándolas de igual forma que el diagrama
        positions = ['Point Guard: base', 'Shooting Guard: escolta', 'Small Forward: alero', 'Power Forward: ala-pivot', 'Center: pivot']
        for number in range(1, 6):
            self.set_x(172)
            self.set_font('times', 'B', 11)
            self.cell(7, 5, str(number) + '. ', 0, 0)
            self.set_font('times', '', 11)
            self.cell(100, 5, positions[number-1])
            self.ln(8)
    
    def roster(self): # Esta función crea una página adjuntando la plantilla del equipo
        self.set_y(17)
        # Establecemos un título
        self.set_text_color(0, 117, 139)
        self.set_font('times', 'B', 13)
        self.cell(0, 10, 'Plantilla Charlotte Hornets - Temporada 2022/2023', align = 'C')
        self.ln(18)
        
        # Incluimos un párrafo explicativo
        self.set_text_color(0)
        self.set_font('times', '', 11)
        roster_text = 'En la imagen adjunta en esta página se muestran todos los jugadores del equipo Charlotte Hornets para la temporada 2022-2023. De cada jugador se especifica su altura, su peso, su edad, el número de años que lleva participando en la NBA y su lugar de nacimiento (el estado si nació en EE.UU. o el país en caso contrario). Las posiciones de cada jugador se especifican en las tablas de las páginas 3 y 4.'
        self.multi_cell(247, 5.5, roster_text, align = 'J')
        self.ln(8)
        # Adjuntamos la imagen que muestra la plantilla con todos los jugadores
        self.image('players_ch.png', x = 50, w = 198)


if __name__ == '__main__':
    # Indicamos el equipo a analizar y la página web de la cual se van a obtener los datos para los pronósticos
    team = 'Charlotte Hornets'
    predictions_url = 'https://www.sportytrader.com/en/odds/basketball/usa/nba-306/'

    # Ejecutamos la ETL de Web Scraping para mostrar los pronósticos de los siguientes partidos por pantalla
    matches = extract_webscraping(predictions_url)
    team_predictions = transform_webscraping(team, matches)
    load_webscraping(team_predictions, team)
    
    
    # Especificamos la temporada y el equipo del cual vamos a crear el informe
    season, team = 2023, 'CHA'
    # Indicamos la información necesaria para acceder a la API
    endpoint = f'https://api.sportsdata.io/v3/nba/stats/json/PlayerSeasonStatsByTeam/{season}/{team}'
    api_key = 'a093e38e3f8c45d492d56260f95843c9' # Se debe incluir aquí la clave del usuario
    headers = {'Ocp-Apim-Subscription-Key': api_key}

    # Ejecutamos la ETL de la API para obtener el informe del equipo en formato PDF
    nba_info = extract_api(endpoint, headers)
    players, shots = transform_api(nba_info)
    load_api(players, shots)