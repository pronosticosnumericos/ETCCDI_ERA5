#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from git import Repo, InvalidGitRepositoryError, NoSuchPathError, GitCommandError

# --------- CONFIG ---------
USERNAME    = "pronosticosnumericos"
REPO_NAME   = "ETCCDI_ERA5"
REPO_PATH   = "/home/sig07/brisia_mapas/concatenados/sitio"  # sin '/' final
DEFAULT_BRANCH = "main"
FORCE_IF_REJECTED = True  # intenta push normal; si es rechazado, fuerza

# Token desde env (PAT clásico con scope 'repo' o token fino con permisos de contenido)
TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    raise RuntimeError("No se encontró la variable de entorno GITHUB_TOKEN.")

REMOTE_URL = f"https://{USERNAME}:{TOKEN}@github.com/{USERNAME}/{REPO_NAME}.git"

# --------- Helpers ---------
def ensure_repo(path: str) -> Repo:
    os.makedirs(path, exist_ok=True)
    try:
        repo = Repo(path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        repo = Repo.init(path)
        print(f"Inicializado repo vacío en: {path}")
    return repo

def ensure_branch(repo: Repo, branch: str):
    # Crea/checkout a 'branch'
    if branch in repo.heads:
        repo.git.checkout(branch)
    else:
        # Si no hay commits, crea rama huérfana
        if repo.head.is_valid():
            repo.git.checkout("-b", branch)
        else:
            # primer commit dummy si estuviera completamente vacío
            open(os.path.join(repo.working_tree_dir, ".gitkeep"), "a").close()
            repo.git.add(A=True)
            repo.index.commit("chore: init repository")
            repo.git.checkout("-b", branch)
    # Config mínimos
    with repo.config_writer() as cw:
        if not cw.has_option("user", "name"):
            cw.set_value("user", "name", USERNAME)
        if not cw.has_option("user", "email"):
            cw.set_value("user", "email", f"{USERNAME}@users.noreply.github.com")

def ensure_remote(repo: Repo, remote_name: str, url: str):
    if remote_name in [r.name for r in repo.remotes]:
        repo.git.remote("set-url", remote_name, url)
    else:
        repo.create_remote(remote_name, url)

def push_with_fallback(repo: Repo, remote_name: str, branch: str, force_if_rejected=True):
    try:
        print(f"Empujando {branch} → {remote_name} (normal)…")
        repo.git.push("-u", remote_name, branch)
        print("Push realizado correctamente.")
    except GitCommandError as e:
        msg = str(e)
        print(f"Push rechazado: {msg}")
        if force_if_rejected:
            print("Reintentando con --force…")
            repo.git.push("--force", "-u", remote_name, branch)
            print("Force push realizado correctamente.")
        else:
            raise

# --------- Main ---------
def main():
    repo = ensure_repo(REPO_PATH)
    ensure_branch(repo, DEFAULT_BRANCH)

    # Añade cambios y commitea solo si hay algo nuevo
    repo.git.add(A=True)
    if repo.is_dirty(untracked_files=True):
        repo.index.commit("Agregar ETCCDI")
        print("Commit creado.")
    else:
        print("No hay cambios para commitear.")

    ensure_remote(repo, "origin", REMOTE_URL)
    push_with_fallback(repo, "origin", DEFAULT_BRANCH, force_if_rejected=FORCE_IF_REJECTED)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ocurrió un error: {e}")

