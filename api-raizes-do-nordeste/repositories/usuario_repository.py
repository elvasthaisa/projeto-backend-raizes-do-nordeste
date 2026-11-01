from repositories.dados_exemplo import USUARIOS


def buscar_por_email(email: str):
    for usuario in USUARIOS:
        if usuario["email"] == email.lower():
            return usuario
    return None

def adicionar(usuario: dict):
    USUARIOS.append(usuario) # Próxima etapa: gravar no banco
