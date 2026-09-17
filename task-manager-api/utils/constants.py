"""Constantes de domínio — única fonte para listas, limites e rótulos usados pela API."""
import re

API_NAME = "Task Manager API"
API_VERSION = "1.0"

# Tasks
VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
CLOSED_STATUSES = ("done", "cancelled")
DEFAULT_STATUS = "pending"
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2                      # prioridade <= 2 conta como "alta" nos relatórios
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}
DATE_FORMAT = "%Y-%m-%d"
TAGS_SEPARATOR = ","

# Usuários
VALID_ROLES = ("user", "admin", "manager")
DEFAULT_ROLE = "user"
MIN_PASSWORD_LENGTH = 4
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$")

# Categorias
DEFAULT_COLOR = "#000000"
COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")

# Relatórios
RECENT_DAYS = 7
