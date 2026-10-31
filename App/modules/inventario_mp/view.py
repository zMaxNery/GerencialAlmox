from __future__ import annotations

import getpass
import tkinter as tk
import os
import tempfile

from datetime import datetime
from decimal import Decimal
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository


class InventarioMP(ctk.CTkFrame):
    """Lançamentos da contagem de MP."""

    