import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Créer le dictionnaire des credentials à partir des variables d'environnement
credentials_dict = {
    "type": os.getenv("GOOGLE_SHEETS_TYPE"),
    "project_id": os.getenv("GOOGLE_SHEETS_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_SHEETS_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_SHEETS_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("GOOGLE_SHEETS_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_SHEETS_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_SHEETS_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_SHEETS_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_SHEETS_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_SHEETS_CLIENT_X509_CERT_URL")
}

# Configuration de l'API Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("DiscordBotConfig")
perms_ws = sheet.worksheet("perms")  # Déjà présent chez toi
access_levels_ws = sheet.worksheet("access_levels")

def get_guild_grade(guild_id: int) -> str | None:
    try:
        guild_id = str(guild_id)
        all_rows = access_levels_ws.get_all_values()
        for row in all_rows:
            if row[0] == guild_id:
                return row[1].lower()  # retourne le grade en minuscules (normal/premium/beta)
        return None  # Aucun accès
    except Exception as e:
        print(f"Erreur lors de la récupération du grade : {e}")
        return None

def get_logs_ws():
    # Autorisation avec l'API Google
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)

    # 🔧 Remplace par l'ID ou le nom correct de ton Google Sheets
    spreadsheet = client.open("DiscordBotConfig")  # ou client.open_by_key("ID_du_Sheet")

    # Accès à la feuille "logs"
    logs_ws = spreadsheet.worksheet("logs")
    return logs_ws

def get_login_ws():
    client = connect_to_google_sheets()
    sheet = client.open("DiscordBotConfig")
    return sheet.worksheet("login_config")

def is_role_allowed_for_command(guild_id: str, command_name: str, user_role_ids: list[int]) -> bool:
    # Extrait les rôles autorisés depuis la feuille Google Sheets
    all_rows = perms_ws.get_all_values()
    for row in all_rows:
        if row[0] == guild_id and row[1] == command_name:
            allowed_ids = row[2].split(",") if len(row) > 2 else []
            return any(str(role_id) in allowed_ids for role_id in user_role_ids)
    return False

# Fonction pour se connecter à Google Sheets
def connect_to_google_sheets():
    # Définir la portée d'accès à l'API Google Sheets et Google Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Utiliser les informations d'identification de service pour l'authentification
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    
    # Se connecter au client Google Sheets
    client = gspread.authorize(creds)
    
    return client

# Ouvrir le fichier Google Sheets "DiscordBotConfig" et accéder à la feuille "logs"
sheet = client.open("DiscordBotConfig").worksheet("logs")

# Fonction pour enregistrer l'ID du salon dans Google Sheets
def save_log_to_google_sheets(guild_id, channel_id):
    all_rows = sheet.get_all_values()
    existing_log = False

    # Vérifier si un log existe déjà pour cette guilde
    for idx, row in enumerate(all_rows):
        if row[0] == str(guild_id):  # Si un salon est déjà défini pour ce serveur
            sheet.update_cell(idx + 1, 2, str(channel_id))  # Mettre à jour l'ID du salon
            existing_log = True
            break

    # Si aucun salon n'est défini pour cette guilde, on l'ajoute
    if not existing_log:
        sheet.append_row([str(guild_id), str(channel_id)])  # Ajouter une nouvelle ligne avec l'ID de la guilde et du salon

# Fonction pour supprimer un log de la feuille Google Sheets
def remove_log_from_google_sheets(guild_id):
    try:
        all_rows = sheet.get_all_values()
        # Rechercher l'index de la ligne contenant la guilde
        row_idx = None
        for idx, row in enumerate(all_rows):
            if row[0] == str(guild_id):
                row_idx = idx + 1  # Gspread est basé sur un index à 1
                break

        if row_idx:
            # Si une ligne est trouvée, réécrire les lignes sans celle-ci
            sheet.delete_rows(row_idx, row_idx)  # Une alternative
            print(f"Log supprimé pour la guilde {guild_id}")
        else:
            print(f"Aucun log trouvé pour la guilde {guild_id}")

    except Exception as e:
        print(f"Erreur lors de la suppression du log: {e}")

# Fonction pour obtenir la configuration de login (salon et rôle) depuis Google Sheets
def get_login_config_from_google_sheets(guild_id):
    try:
        # Se connecter à Google Sheets
        client = connect_to_google_sheets()
        sheet = client.open("DiscordBotConfig").worksheet("login_config")

        # Chercher les logs pour la guilde spécifiée
        all_rows = sheet.get_all_values()
        for row in all_rows:
            if row[0] == str(guild_id):  # Si la guilde correspond
                salon_id = row[1]
                role_id = row[2]
                return salon_id, role_id
        
        return None  # Aucun log trouvé pour cette guilde
    except Exception as e:
        print(f"Erreur lors de la récupération de la configuration de login: {e}")
        return None
    
def get_log_channel_id(guild_id: str) -> Optional[int]:
    logs_ws = get_logs_ws()  # logs_ws est déjà une worksheet
    for row in logs_ws.get_all_values():
        if row[0] == guild_id:
            return int(row[1])
    return None

def get_log_channel_id(guild_id: str) -> Optional[int]:
    logs_ws = get_logs_ws()
    for row in logs_ws.get_all_values():
        if row[0] == guild_id:
            return int(row[1])
    return None

def get_worksheet(sheet_name):
    try:
        client = connect_to_google_sheets()
        sheet = client.open("DiscordBotConfig")
        return sheet.worksheet(sheet_name)
    except Exception as e:
        print(f"Erreur lors de la récupération de la feuille '{sheet_name}': {e}")
        return None
    
def get_all_worksheets():
    try:
        client = connect_to_google_sheets()
        sheet = client.open("DiscordBotConfig")
        return sheet.worksheets()  # Retourne une liste de toutes les feuilles de calcul
    except Exception as e:
        print(f"Erreur lors de la récupération de toutes les feuilles: {e}")
        return []