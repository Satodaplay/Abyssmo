import discord
import random
import pandas as pd
import csv
import time
import asyncio

#         _____     ____
#        /      \  |  o | 
#       |        |/ ___\| 
#       |_________/     
#       |_|_| |_|_|

# Configura el cliente de Discord con las intenciones especificadas
intents = discord.Intents.all()
intents.voice_states = True
client = discord.Client(intents=intents)

#<------------------------------------------------------------------------------------------>
#<------------------------------------funciones--------------------------------------------->
#<------------------------------------------------------------------------------------------>

# Carga la base de datos desde un archivo CSV
def load_database(csv_file):
    return pd.read_csv(csv_file)

# Guarda el matrimonio en un archivo CSV
def save_marriage(user_id, character_index):
    with open('marriages.csv', 'a', newline='') as csvfile:
        fieldnames = ['user_id', 'character_index', 'marriage_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Si el archivo está vacío, escribe los encabezados
        if csvfile.tell() == 0:
            writer.writeheader()

        writer.writerow({'user_id': user_id, 'character_index': character_index, 'marriage_time': time.time()})

# Obtiene los personajes con los que el usuario está casado desde el archivo CSV
def get_marriages(user_id):
    marriages = []
    with open('marriages.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['user_id'] == user_id:
                marriages.append(int(row['character_index']))
    return marriages

# Elimina el matrimonio en el archivo CSV
def remove_marriage(user_id, character_index):
    marriages = []
    with open('marriages.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        for row in rows:
            if row['user_id'] == user_id and int(row['character_index']) == character_index:
                rows.remove(row)
                break
    with open('marriages.csv', 'w', newline='') as csvfile:
        fieldnames = ['user_id', 'character_index', 'marriage_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# Verifica si el personaje ya está casado con otro usuario
def is_married(character_index):
    with open('marriages.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if int(row['character_index']) == character_index:
                return True
    return False

# Verifica si el usuario puede casarse nuevamente (después de 2 horas)
def can_marry_again(user_id):
    with open('marriages.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['user_id'] == user_id:
                marriage_time = float(row['marriage_time'])
                if time.time() - marriage_time < CASAMIENTO_COOLDOWN:
                    return False
    return True

def combatir(personaje1, personaje2):
    # Obtener el valor numérico de la rareza utilizando el diccionario
    rareza1 = rareza_valor[personaje1['Rareza']]
    rareza2 = rareza_valor[personaje2['Rareza']]

    # Calcula los resultados del combate
    resultado1 = random.randint(1, 100) + 5 * rareza1
    resultado2 = random.randint(1, 100) + 5 * rareza2

    if resultado1 > resultado2:
        ganador = personaje1
        perdedor = personaje2
    else:
        ganador = personaje2
        perdedor = personaje1

    # Seleccionar ataques aleatorios para ambos personajes
    ataque_ganador = random.choice(ataques)
    ataque_perdedor = random.choice(ataques)

    return ganador, perdedor, ataque_ganador, ataque_perdedor

def create_character_embed(character):
    # Definir colores por rareza
    rarity_color = {
        '⚪comun⚪': discord.Color.light_gray(),
        '🟢raro🟢': discord.Color.green(),
        '🔵super raro🔵': discord.Color.blue(),
        '🟣epico🟣': discord.Color.purple(),
        '🟡legendario🟡': discord.Color.gold(),
        '🟠mitico🟠': discord.Color.orange(),
        '🌟definitivo🌟': discord.Color.red()
    }
    color = rarity_color.get(character["Rareza"], discord.Color.light_gray())

    embed = discord.Embed(title=character["Nombre"], description=f"Serie: {character['Serie']} \nRareza: {character['Rareza']}", color=color)
    embed.set_image(url=character["Foto"])
    embed.add_field(name="Descripción", value=character.get("Descripción", "No disponible"), inline=False)
    return embed

async def send_character_carousel(message, characters):
    if characters:
        current_index = 0
        msg = await message.channel.send(embed=create_character_embed(characters[current_index]))
        await msg.add_reaction('⬅️')
        await msg.add_reaction('➡️')

        def check(reaction, user):
            return user == message.author and str(reaction.emoji) in ['⬅️', '➡️'] and reaction.message.id == msg.id

        while True:
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                if str(reaction.emoji) == '➡️':
                    current_index = (current_index + 1) % len(characters)
                elif str(reaction.emoji) == '⬅️':
                    current_index = (current_index - 1) % len(characters)

                await msg.edit(embed=create_character_embed(characters[current_index]))
                await msg.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break
        await msg.clear_reactions()
    else:
        await message.channel.send(f"{message.author.mention} no hay personajes disponibles.")

def create_help_embed():
    embed = discord.Embed(
        title="🤖 Ayuda de Mudae 🤖",
        description="Aquí puedes encontrar los comandos disponibles para interactuar con el bot.",
        color=discord.Color.blue()  # Puedes cambiar el color aquí
    )
    embed.add_field(
        name="Comandos Básicos",
        value=(
            "`$invocar` - Invoca un personaje aleatorio del abismo.\n"
            "`$casados` - Muestra con qué personajes estás casado, con opciones para navegar.\n"
            "`$divorciarse` - Permite divorciarse de un personaje casado.\n"
            "`$intercambiar` - Inicia un proceso para intercambiar personajes con otro usuario.\n"
            "`$combate` - Combate con un personaje contra el de otro usuario.\n"
            "`$personajes` - Muestra todos los personajes disponibles para ver y navegar entre ellos.\n"
        ),
        inline=False
    )
    embed.add_field(
        name="Información Adicional",
        value="Esclavízalos a todos, ¡cabrón!",
        inline=False
    )
    embed.set_footer(text="Mudae Bot | Ayuda")
    return embed

def weighted_character_index(database):
    weights = []
    for index, row in database.iterrows():
        # Asigna pesos basados en la probabilidad de rareza
        probability = probabilidades_rareza[row['Rareza']]
        weights.append(probability)
    
    # Escoge un índice de personaje basado en los pesos
    return random.choices(range(len(database)), weights, k=1)[0]

#<------------------------------------------------------------------------------------------>
#<-------------------------------------variables-------------------------------------------->
#<------------------------------------------------------------------------------------------>

PREFIX = "$"

# Define el token de tu bot
TOKEN = ''

# Carga la base de datos al iniciar el bot
database = load_database('personajes.csv')

# Diccionario para realizar un seguimiento de las invocaciones de cada usuario
invocation_tracker = {}

# Tiempo en segundos entre cada invocación permitida
INVOCATION_COOLDOWN = 3600  # 1 hora

# Invoaciones maximas en de tirada antes del cooldown
INVOCATION_MAX = 10

# Tiempo en segundos entre cada casamiento permitida
CASAMIENTO_COOLDOWN = 7200  # 2 horas

# Lista de ataques posibles
ataques = [
    "Golpe Fuerte",
    "Patada Alta",
    "Rayo Energético",
    "Defensa Mágica",
    "Espada de Luz",
    "Lanzamiento de Spaghetti",
    "Danza de Confusión",
    "Ataque Telepático del Pollo",
    "Destello del Unicornio",
    "Estornudo Explosivo",
    "Salto Cuántico",
    "Lluvia de Donas",
    "Mordisco del Espacio-Tiempo",
    "Transformación en Almohada",
    "Canto de las Sirenas de Internet",
    "Revolución de Pizza",
    "Golpe de Tofu",
    "Mirada Fulminante de Gato",
    "Beso de Llama",
    "Burbuja de Jabón Letal",
    "Olas de Melodía",
    "Carrera de Caracoles",
    "Invocación del Espíritu de la Cafetería",
    "Arrojo de Gelatina",
    "Caída de Meteoritos de Peluche",
    "Patada de la Energía Cósmica",
    "Oso Abrazador",
    "Cataclismo de Galletas",
    "Chasquido del Destino",
    "Cascada de Chocolate",
    "Ráfaga de Papel Higiénico",
    "Despertar del Pato de Goma",
    "Hipnosis del Helado",
    "Tormenta de Confeti",
    "Exhalación del Dragón de Comedia",
    "Implosión de Novelas Románticas",
    "Choque de Calcetines Perdidos",
    "Rugido del Monstruo de Debajo de la Cama",
    "Lanzamiento de Calabazas Enfurecidas",
    "Soplido de Polvo Cósmico",
    "Teletransporte de Sandía",
    "Granizo de Palomitas de Maíz",
    "Furia de los Cien Hamsters",
    "Picadura de la Medusa de Jalea",
    "Eclipse de Queso",
    "Emboscada de Libros Voladores",
    "Torbellino de Té Helado",
    "Maldición del Karaoke Eterno",
    "Resplandor del Arcoíris Ninja",
    "Llamada del Koala Bostezante",
    "Confusión de Calcetines Giratorios",
    "Barrido de Pan Baguette",
    "Chorro de Salsa Picante",
    "Vórtice de Caramelos Ácidos",
    "Aliento Gélido de Menta",
    "Retorcimiento de Dimensiones",
    "Cañonazo de Tomates Podridos",
    "Ataque de los Clones de Gelatina",
    "Explosión de Glitter",
    "Ritual del Té Verde",
    "Desfile de los Patos Mareados",
    "Lanzamiento de Huevos de Pascua",
    "Desintegración por Chocolate",
    "Saqueo Pirata de Papel",
    "Terremoto de Gel",
    "Ola de Puzzles",
    "Avalancha de Almohadas",
    "Zarpazo de Oso de Goma",
    "Inundación de Sopa de Letras",
    "Grito de los Mil Delfines",
    "Abrazo de Koala Electrizante",
    "Mazazo de Macarrones",
    "Ráfaga de Té de Burbujas",
    "Apocalipsis de Pegatinas",
    "Beso Explosivo de Pez Globo",
    "Tornado de Pelusas",
    "Invasión de los Robots de Papel",
    "Carrera de Tortugas Ninja",
    "Lanzallamas de Nubes",
    "Jardín de Flores Carnívoras",
    "Emboscada de Sushi Volador",
    "Hechizo de Lluvia de Café",
    "Pulso Psíquico de Panqueques",
    "Lluvia de Estrellas Fugaces",
    "Danza del Disco Destructivo",
    "Congelación Instantánea de Limonada",
    "Chubasco de Malvaviscos",
    "Asalto del Escuadrón Pingüino",
    "Salpicadura de Salsa de Soja",
    "Escupitajo de Fuego de Dragón",
    "Intervención de Conejitos Fofos",
    "Impulso de Patineta Voladora",
    "Destrucción de Hamburguesas",
    "Acumulación de Nieve de Algodón de Azúcar",
    "Rugido del León Marítimo",
    "Estruendo de Vinilos",
    "Festival de Paellas Voladoras",
    "Invocación del Anciano de los Videojuegos",
    "Estampida de Caballos de Papel",
    "Explosión de Bayas Heladas"
]

# Diccionario de rareza a valor numérico
rareza_valor = {
    '⚪comun⚪': 1,
    '🟢raro🟢': 5,
    '🔵super raro🔵': 10,
    '🟣epico🟣': 15,
    '🟡legendario🟡': 20,
    '🟠mitico🟠': 25,
    '🌟definitivo🌟': 30
}

# Probabilidades de rareza en porcentajes
probabilidades_rareza = {
    '⚪comun⚪': 50,      # 50%
    '🟢raro🟢': 20,       # 20%
    '🔵super raro🔵': 15,  # 15%
    '🟣epico🟣': 8,       # 8%
    '🟡legendario🟡': 4,   # 4%
    '🟠mitico🟠': 2,       # 2%
    '🌟definitivo🌟': 1    # 1%
}

#<------------------------------------------------------------------------------------------>
#<-------------------------------------Comandos--------------------------------------------->
#<------------------------------------------------------------------------------------------>

@client.event
async def on_ready():
    print('Bot está listo')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(PREFIX + 'invocar'):
        user_id = str(message.author.id)
        current_time = time.time()

        # Verificar si el usuario tiene cooldown activo
        if user_id in invocation_tracker:
            invocations_in_last_hour = [
                invocation_time for invocation_time in invocation_tracker[user_id]
                if current_time - invocation_time <= INVOCATION_COOLDOWN
            ]
            if len(invocations_in_last_hour) >= INVOCATION_MAX:
                last_invocation_time = invocations_in_last_hour[-1]
                remaining_time = INVOCATION_COOLDOWN - (current_time - last_invocation_time)
                minutes, seconds = divmod(remaining_time, 60)
                await message.channel.send(f"No puedes invocar personajes tan seguido. Debes esperar {int(minutes)} minutos y {int(seconds)} segundos.")
                return

        # Escoger un personaje basado en la ponderación de rareza
        character_index = weighted_character_index(database)
        character = database.iloc[character_index]

        # Verificar si el personaje ya está casado
        if is_married(character_index):
            await message.channel.send(f'Lo siento, {message.author.mention}, pero {character["Nombre"]} de {character["Serie"]} ya está casado.\n{character["Foto"]}')
            return

        # Enviar el embebido del personaje
        invoc_embed = create_character_embed(character)
        invoc_msg = await message.channel.send(embed=invoc_embed)
        await invoc_msg.add_reaction("💍")

        # Registrar la invocación en el tracker
        if user_id not in invocation_tracker:
            invocation_tracker[user_id] = []
        invocation_tracker[user_id].append(current_time)

        # Esperar por una reacción para casar al personaje
        def check(reaction, user):
            return user != client.user and str(reaction.emoji) == "💍" and reaction.message.id == invoc_msg.id

        try:
            reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            user_id_reacting = str(user.id)
            if can_marry_again(user_id_reacting) and not is_married(character_index):
                save_marriage(user_id_reacting, character_index)
                await message.channel.send(f'{user.mention} se ha casado con {character["Nombre"]} de {character["Serie"]}')
            else:
                await message.channel.send(f"{user.mention}, no puedes casarte con {character['Nombre']} ahora. Podría estar ya casado o necesitas esperar para casarte de nuevo.")
        except asyncio.TimeoutError:
            print("¡Se acabó el tiempo para casarse con este personaje!")

        # Borrar la reacción después del evento
        await invoc_msg.clear_reactions()

    if message.content.startswith(PREFIX + 'casados'):
        # Procesar el mensaje para determinar el usuario del que se quiere ver los casamientos
        args = message.content.split()
        target_user = message.mentions[0] if len(args) > 1 and message.mentions else message.author
        user_id = str(target_user.id)

        # Obtener los índices de los personajes con los que el usuario está casado
        marriages = get_marriages(user_id)
        
        if not marriages:
            await message.channel.send(f"{target_user.mention} no está casado/a con ningún personaje.")
        else:
            # Obtener los registros de personajes casados desde la base de datos
            married_characters = [database.iloc[index] for index in marriages]
            # Enviar el carrusel de personajes
            await send_character_carousel(message, married_characters)

    elif message.content.startswith(PREFIX + 'divorciarse'):
        user_id = str(message.author.id)
        marriages = get_marriages(user_id)
        if marriages:
            married_characters = [database.iloc[index]["Nombre"] for index in marriages]
            marriages_str = "\n".join([f"{i+1}. {name}" for i, name in enumerate(married_characters)])
            await message.channel.send(f"{message.author.mention}, ¿de qué personaje te gustaría divorciarte?\n{marriages_str}")

            def check(m):
                return m.author == message.author and m.content.isdigit() and 1 <= int(m.content) <= len(married_characters)

            response = await client.wait_for('message', timeout=30.0, check=check)
            selected_index = int(response.content) - 1
            selected_character_index = marriages[selected_index]
            selected_character_name = database.iloc[selected_character_index]["Nombre"]
            remove_marriage(user_id, selected_character_index)
            await message.channel.send(f"{message.author.mention} te has divorciado de {selected_character_name}.")

        else:
            await message.channel.send(f"{message.author.mention}, no estás casado con ningún personaje.")

    elif message.content.startswith(PREFIX + 'intercambiar'):
        user_id = str(message.author.id)
        marriages = get_marriages(user_id)
        
        if not marriages:
            await message.channel.send(f"{message.author.mention}, no estás casado con ningún personaje.")
            return
        
        married_characters = [database.iloc[index]["Nombre"] for index in marriages]
        marriages_str = "\n".join([f"{i+1}. {name}" for i, name in enumerate(married_characters)])
        await message.channel.send(f"{message.author.mention}, ¿con qué personaje te gustaría intercambiar?\n{marriages_str}")
        
        def check(m):
            return m.author == message.author and m.content.isdigit() and 1 <= int(m.content) <= len(married_characters)
        
        response = await client.wait_for('message', timeout=30.0, check=check)
        selected_index = int(response.content) - 1
        selected_character_index = marriages[selected_index]
        selected_character_name = database.iloc[selected_character_index]["Nombre"]
        
        await message.channel.send(f"{message.author.mention}, has seleccionado intercambiar con {selected_character_name}. Por favor menciona al usuario con quien deseas intercambiar.")
        
        def check_user(m):
            return m.author == message.author and m.mentions
        
        response_user = await client.wait_for('message', timeout=30.0, check=check_user)
        target_user_id = str(response_user.mentions[0].id)
        
        target_marriages = get_marriages(target_user_id)
        if not target_marriages:
            await message.channel.send(f"{message.author.mention}, {response_user.mentions[0].mention} no está casado con ningún personaje.")
            return
        
        married_characters_target = [database.iloc[index]["Nombre"] for index in target_marriages]
        marriages_str_target = "\n".join([f"{i+1}. {name}" for i, name in enumerate(married_characters_target)])
        await message.channel.send(f"{response_user.mentions[0].mention}, ¿con qué personaje te gustaría intercambiar?\n{marriages_str_target}")
        
        def check_target(m):
            return m.author == response_user.mentions[0] and m.content.isdigit() and 1 <= int(m.content) <= len(married_characters_target)
        
        response_target = await client.wait_for('message', timeout=30.0, check=check_target)
        selected_index_target = int(response_target.content) - 1
        selected_character_index_target = target_marriages[selected_index_target]
        selected_character_name_target = database.iloc[selected_character_index_target]["Nombre"]
                
        # Realizar el intercambio
        remove_marriage(user_id, selected_character_index)
        remove_marriage(target_user_id, selected_character_index_target)
            
        save_marriage(user_id, selected_character_index_target)
        save_marriage(target_user_id, selected_character_index)
            
        await message.channel.send(f"¡Intercambio completado! {message.author.mention} ahora está casado con {selected_character_name_target} y {response_user.mentions[0].mention} está casado con {selected_character_name}.")

    if message.content.startswith(PREFIX + 'combate'):
        user_id = str(message.author.id)
        marriages = get_marriages(user_id)

        if not marriages:
            await message.channel.send(f"{message.author.mention}, no tienes personajes con los que combatir.")
            return

        # Listar personajes del usuario
        married_characters = [database.iloc[index] for index in marriages]
        married_characters_str = "\n".join([f"{i+1}. {char['Nombre']} de {char['Serie']}" for i, char in enumerate(married_characters)])
        await message.channel.send(f"{message.author.mention}, selecciona un personaje para combatir:\n{married_characters_str}")

        def check(m):
            return m.author == message.author and m.content.isdigit() and 1 <= int(m.content) <= len(married_characters)

        response = await client.wait_for('message', timeout=30.0, check=check)
        selected_index = int(response.content) - 1
        personaje1 = married_characters[selected_index]

        # Solicitar al usuario mencionar a otro usuario para combatir
        await message.channel.send(f"{message.author.mention}, menciona al usuario con quien deseas combatir.")

        def check_user(m):
            return m.author == message.author and m.mentions

        response_user = await client.wait_for('message', timeout=60.0, check=check_user)
        target_user = response_user.mentions[0]
        target_user_id = str(target_user.id)
        target_marriages = get_marriages(target_user_id)

        if not target_marriages:
            await message.channel.send(f"{target_user.mention} no tiene personajes con los que combatir.")
            return

        # Listar personajes del usuario mencionado
        target_characters = [database.iloc[index] for index in target_marriages]
        target_characters_str = "\n".join([f"{i+1}. {char['Nombre']} de {char['Serie']}" for i, char in enumerate(target_characters)])
        await message.channel.send(f"{target_user.mention}, elige un personaje para defender:\n{target_characters_str}")

        def check_target(m):
            return m.author.id == target_user.id and m.content.isdigit() and 1 <= int(m.content) <= len(target_characters)
        
        response_target = await client.wait_for('message', timeout=30.0, check=check_target)
        selected_index_target = int(response_target.content) - 1
        personaje2 = target_characters[selected_index_target]

        # Realizar el combate
        ganador, perdedor, ataque_ganador, ataque_perdedor = combatir(personaje1, personaje2)

        # Enviar los resultados del combate
        resultado_msg = f"🥊 Combate entre {personaje1['Nombre']} de {personaje1['Serie']} y {personaje2['Nombre']} de {personaje2['Serie']} 🥊\n"
        resultado_msg += f"{personaje1['Nombre']} usa {ataque_ganador}! 🗡️\n"
        resultado_msg += f"{personaje2['Nombre']} responde con {ataque_perdedor}! 🛡️\n"
        resultado_msg += f"🏆 {ganador['Nombre']} gana el combate! 🏆\n"
        await message.channel.send(resultado_msg)

    if message.content.startswith(PREFIX + 'help'):
        help_embed = create_help_embed()
        await message.channel.send(embed=help_embed)

    if message.content.startswith(PREFIX + 'personajes'):
        # Eliminar el prefijo y dividir el comando para obtener posibles argumentos
        args = message.content[len(PREFIX) + len('personajes'):].strip().split()
        
        if len(args) == 0:
            # Si no se proporciona la serie, mostrar todos los personajes
            all_characters = database.to_dict('records')
            await send_character_carousel(message, all_characters)
            return
        
        # Si el usuario pide listar todas las series
        if args[0].lower() == 'list':
            series_list = database['Serie'].drop_duplicates().sort_values()
            series_embed = discord.Embed(title="Series Disponibles", description="\n".join(series_list), color=discord.Color.blue())
            await message.channel.send(embed=series_embed)
            return
        
        # Unir todos los argumentos para formar el nombre de la serie
        series_name = ' '.join(args).strip()
        
        # Filtrar la base de datos para obtener personajes de esa serie específica
        series_characters = database[database['Serie'].str.lower() == series_name.lower()]
        
        if series_characters.empty:
            await message.channel.send(f"No se encontraron personajes de la serie '{series_name}'.")
        else:
            # Convertir el DataFrame filtrado a una lista de diccionarios
            characters_list = series_characters.to_dict('records')
            # Enviar el carrusel de personajes
            await send_character_carousel(message, characters_list)

client.run(TOKEN)
