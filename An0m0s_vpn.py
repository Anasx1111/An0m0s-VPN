#!/usr/bin/env python3
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import threading
import time
import sys
import math
import re
import shutil
import tempfile
import requests
import json
import webbrowser
import pwd

def check_root():
    """Check if running with root privileges"""
    if os.geteuid() != 0:
        # Silently restart with elevated privileges
        try:
            # Use pkexec and pass GUI env so the window can open as root
            display = os.environ.get('DISPLAY', '')
            xauth = os.environ.get('XAUTHORITY', '')
            args = ['pkexec', 'env', f'DISPLAY={display}', f'XAUTHORITY={xauth}', sys.executable] + sys.argv
            os.execvp('pkexec', args)
        except Exception as e:
            sys.exit(1)

class An0m0sVPN:
    def __init__(self, root):
        self.root = root
        self.root.title("An0m0s VPN")
        
        # Get screen dimensions for responsive design
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate window size (80% of screen or max values)
        window_width = min(int(screen_width * 0.8), 1000)
        window_height = min(int(screen_height * 0.85), 800)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        # Set minimum window size (responsive to screen size)
        min_width = min(700, int(screen_width * 0.5))
        min_height = min(550, int(screen_height * 0.5))
        self.root.minsize(min_width, min_height)
        
        # Configuration
        self.ovpn_file = None
        self.vpn_process = None
        self.vpn_pid = None
        self.status_check_thread = None
        self.is_running = False
        self.killswitch_enabled = False
        self._iptables_backup_path = None
        self.current_ip = "Not Connected"
        self.current_country = "Unknown"
        
        # Premium Theme (dark, restrained, high-contrast)
        self.bg_primary = "#0B0F14"        # App background
        self.bg_secondary = "#0F172A"      # Elevated surfaces
        self.bg_card = "#111827"           # Card surface
        self.border_subtle = "#1F2937"     # Subtle borders
        self.border_strong = "#334155"     # Stronger borders

        self.accent_primary = "#38BDF8"    # Sky
        self.accent_secondary = "#A78BFA"  # Violet
        self.accent_success = "#34D399"    # Emerald
        self.accent_danger = "#FB7185"     # Rose
        self.accent_warning = "#FBBF24"    # Amber

        self.text_primary = "#E5E7EB"      # Slate-200
        self.text_secondary = "#94A3B8"    # Slate-400
        self.text_tertiary = "#64748B"     # Slate-500

        self.animation_running = True
        self._pulse_phase = 0
        
        self.root.configure(bg=self.bg_primary)

        # Typography (cross-platform; prefer modern Linux fonts)
        self.font_family = self._choose_font_family([
            "Inter",
            "SF Pro Display",
            "Segoe UI",
            "Noto Sans",
            "Ubuntu",
            "DejaVu Sans",
            "Arial",
        ])
        screen_width = self.root.winfo_screenwidth()
        base_size = max(10, min(12, int(screen_width / 120)))
        self.font_base = tkfont.Font(family=self.font_family, size=base_size)
        self.font_small = tkfont.Font(family=self.font_family, size=max(9, base_size - 1))
        self.font_micro = tkfont.Font(family=self.font_family, size=max(8, base_size - 2))
        self.font_title = tkfont.Font(family=self.font_family, size=max(22, min(34, int(screen_width / 34))), weight="bold")
        self.font_h2 = tkfont.Font(family=self.font_family, size=max(12, base_size + 2), weight="bold")
        self.font_h3 = tkfont.Font(family=self.font_family, size=max(11, base_size + 1), weight="bold")
        self.font_button = tkfont.Font(family=self.font_family, size=base_size, weight="bold")
        self.font_button_small = tkfont.Font(family=self.font_family, size=max(9, base_size - 1), weight="bold")

        # Consistent spacing
        self.space_xs = 6
        self.space_sm = 10
        self.space_md = 16
        self.space_lg = 22
        self.space_xl = 30
        
        # Configure ttk scrollbar style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", 
                       background=self.bg_secondary,
                       troughcolor=self.bg_primary,
                       bordercolor=self.bg_primary,
                       arrowcolor=self.text_secondary,
                       darkcolor=self.bg_secondary,
                       lightcolor=self.bg_secondary)
        
        # Create main container with scrollbar
        self.main_container = tk.Frame(self.root, bg=self.bg_primary)
        self.main_container.pack(fill="both", expand=True)
        
        # Create canvas for scrolling
        self.canvas = tk.Canvas(self.main_container, bg=self.bg_primary, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_primary)
        
        # Configure scroll region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas with proper width binding
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        # Make canvas responsive to window resize
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Responsive layout (debounced reflow)
        self._ui_layout_mode = None
        self._resize_after_id = None
        self.root.bind("<Configure>", self._on_root_configure)

        self._render_ui(force=True)
        self.update_status()
        self.start_animations()

    def _choose_font_family(self, preferred_families):
        try:
            families = set(tkfont.families(self.root))
            for family in preferred_families:
                if family in families:
                    return family
        except Exception:
            pass
        return "TkDefaultFont"

    def _hex_to_rgb(self, value):
        value = value.lstrip('#')
        return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def _blend(self, c1, c2, t):
        r1, g1, b1 = self._hex_to_rgb(c1)
        r2, g2, b2 = self._hex_to_rgb(c2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return self._rgb_to_hex((r, g, b))

    def _open_url(self, url: str):
        """Open a URL safely.

        When running the app as root (pkexec), launching Chromium-based browsers
        often fails due to sandbox restrictions. In that case, try to open the
        URL as the original non-root user via xdg-open.
        """

        def copy_to_clipboard():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
                self.root.update_idletasks()
            except Exception:
                pass

        try:
            if os.geteuid() != 0:
                webbrowser.open_new_tab(url)
                return

            # Running as root: try to detect the original user.
            username = None
            for key in ("SUDO_USER", "PKEXEC_USER"):
                val = os.environ.get(key)
                if val:
                    username = val
                    break
            if not username:
                for key in ("SUDO_UID", "PKEXEC_UID"):
                    val = os.environ.get(key)
                    if val and str(val).isdigit():
                        try:
                            username = pwd.getpwuid(int(val)).pw_name
                            break
                        except Exception:
                            pass

            if username:
                display = os.environ.get("DISPLAY", "")
                xauth = os.environ.get("XAUTHORITY", "")
                cmd = [
                    "sudo",
                    "-u",
                    username,
                    "env",
                    f"DISPLAY={display}",
                    f"XAUTHORITY={xauth}",
                    "xdg-open",
                    url,
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return

            # Fallback: copy + show the URL.
            copy_to_clipboard()
            messagebox.showinfo(
                "Open link",
                "You're running as root, so the browser may refuse to start.\n"
                "The link was copied to clipboard:\n\n" + url,
            )
        except Exception:
            copy_to_clipboard()
            messagebox.showerror(
                "Open link failed",
                "Could not open the link in your browser.\n"
                "The link was copied to clipboard:\n\n" + url,
            )
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
    
    def _on_canvas_configure(self, event):
        """Handle canvas resize to make content responsive"""
        # Update the width of the scrollable frame to match canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_root_configure(self, event):
        if event.widget is not self.root:
            return
        if self._resize_after_id is not None:
            try:
                self.root.after_cancel(self._resize_after_id)
            except Exception:
                pass
        self._resize_after_id = self.root.after(140, self._render_ui)

    def _current_layout_width(self):
        width = int(self.root.winfo_width() or 0)
        if width <= 1:
            width = int(self.root.winfo_screenwidth())
        return width

    def _update_typography(self, width):
        base_size = max(10, min(13, int(width / 115)))
        title_size = max(20, min(36, int(width / 28)))
        try:
            self.font_base.configure(size=base_size)
            self.font_small.configure(size=max(9, base_size - 1))
            self.font_micro.configure(size=max(8, base_size - 2))
            self.font_title.configure(size=title_size)
            self.font_h2.configure(size=max(12, base_size + 2))
            self.font_h3.configure(size=max(11, base_size + 1))
            self.font_button.configure(size=base_size)
            self.font_button_small.configure(size=max(9, base_size - 1))
        except Exception:
            pass

    def _clear_frame(self, frame):
        for child in list(frame.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass

    def _render_ui(self, force=False):
        width = self._current_layout_width()
        self._update_typography(width)

        mode = "2col" if width >= 980 else "1col"
        if not force and mode == self._ui_layout_mode:
            return

        self._ui_layout_mode = mode
        self._clear_frame(self.scrollable_frame)
        self.setup_ui(layout_width=width)
        self.update_status()
        self._sync_config_label()
        self._sync_toggle_visual()
    
    def setup_ui(self, layout_width=None):
        width = int(layout_width or self._current_layout_width())
        content_padx = max(self.space_md, min(self.space_xl, int(width / 40)))

        # App header
        header = tk.Frame(self.scrollable_frame, bg=self.bg_primary)
        header.pack(fill="x", padx=content_padx, pady=(self.space_md, self.space_sm))

        header_left = tk.Frame(header, bg=self.bg_primary)
        header_left.pack(side="left", fill="x", expand=True)

        title_stack = tk.Frame(header_left, bg=self.bg_primary)
        title_stack.pack(side="left", fill="x", expand=True)

        tk.Label(
            title_stack,
            text="An0m0s VPN",
            bg=self.bg_primary,
            fg=self.text_primary,
            font=self.font_title,
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            title_stack,
            text="Enterprise-grade OpenVPN controller • Killswitch firewall",
            bg=self.bg_primary,
            fg=self.text_secondary,
            font=self.font_small,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        header_right = tk.Frame(header, bg=self.bg_primary)
        header_right.pack(side="right", padx=(self.space_md, 0))

        self.connection_pill = tk.Label(
            header_right,
            text="DISCONNECTED",
            bg=self._blend(self.bg_secondary, self.bg_primary, 0.35),
            fg=self.text_secondary,
            font=self.font_button_small,
            padx=14,
            pady=8,
        )
        self.connection_pill.pack(anchor="e")

        divider = tk.Frame(self.scrollable_frame, bg=self.border_subtle, height=1)
        divider.pack(fill="x", padx=content_padx, pady=(0, self.space_lg))

        # Two-column responsive layout (based on current window width)
        is_two_column = width >= 980

        grid = tk.Frame(self.scrollable_frame, bg=self.bg_primary)
        grid.pack(fill="both", expand=True, padx=content_padx)
        grid.grid_columnconfigure(0, weight=1, uniform="col")
        if is_two_column:
            grid.grid_columnconfigure(1, weight=1, uniform="col")

        # Left column
        left = tk.Frame(grid, bg=self.bg_primary)
        left.grid(row=0, column=0, sticky="nsew")

        # Right column
        right = tk.Frame(grid, bg=self.bg_primary)
        if is_two_column:
            right.grid(row=0, column=1, sticky="nsew", padx=(self.space_lg, 0))
        else:
            right.grid(row=1, column=0, sticky="nsew", pady=(self.space_lg, 0))

        # Connection status card
        status_card = tk.Frame(left, bg=self.bg_card, highlightbackground=self.border_subtle, highlightthickness=1)
        status_card.pack(fill="x", pady=(0, self.space_lg))

        status_inner = tk.Frame(status_card, bg=self.bg_card)
        status_inner.pack(fill="x", padx=self.space_lg, pady=self.space_lg)

        status_head = tk.Frame(status_inner, bg=self.bg_card)
        status_head.pack(fill="x")

        tk.Label(
            status_head,
            text="CONNECTION",
            bg=self.bg_card,
            fg=self.text_tertiary,
            font=self.font_micro,
        ).pack(side="left")

        self.refresh_ip_btn = tk.Button(
            status_head,
            text="Refresh",
            font=self.font_button_small,
            bg=self.bg_secondary,
            fg=self.text_primary,
            activebackground=self._blend(self.bg_secondary, self.text_primary, 0.08),
            activeforeground=self.text_primary,
            cursor="hand2",
            padx=12,
            pady=6,
            relief="flat",
            borderwidth=0,
            command=self.refresh_ip_info,
        )
        self.refresh_ip_btn.pack(side="right")
        self.add_button_hover(self.refresh_ip_btn, self.bg_secondary, self._blend(self.bg_secondary, self.text_primary, 0.10))

        tk.Label(
            status_inner,
            text="Public IP & Location",
            bg=self.bg_card,
            fg=self.text_primary,
            font=self.font_h2,
            anchor="w",
        ).pack(anchor="w", pady=(self.space_sm, self.space_sm))

        info_box = tk.Frame(status_inner, bg=self.bg_secondary, highlightbackground=self.border_subtle, highlightthickness=1)
        info_box.pack(fill="x")
        info_box_inner = tk.Frame(info_box, bg=self.bg_secondary)
        info_box_inner.pack(fill="x", padx=self.space_md, pady=self.space_md)

        def info_row(parent, label_text):
            row = tk.Frame(parent, bg=self.bg_secondary)
            row.pack(fill="x", pady=4)

            # Small-width layout: stack label above value for readability
            if width < 640:
                tk.Label(
                    row,
                    text=label_text,
                    bg=self.bg_secondary,
                    fg=self.text_secondary,
                    font=self.font_micro,
                    anchor="w",
                ).pack(side="top", anchor="w")
                value = tk.Label(
                    row,
                    text="",
                    bg=self.bg_secondary,
                    fg=self.text_primary,
                    font=self.font_base,
                    anchor="w",
                )
                value.pack(side="top", anchor="w", fill="x")
                return value

            tk.Label(
                row,
                text=label_text,
                bg=self.bg_secondary,
                fg=self.text_secondary,
                font=self.font_small,
                width=14,
                anchor="w",
            ).pack(side="left")
            value = tk.Label(
                row,
                text="",
                bg=self.bg_secondary,
                fg=self.text_primary,
                font=self.font_base,
                anchor="w",
            )
            value.pack(side="left", fill="x", expand=True)
            return value

        self.ip_label = info_row(info_box_inner, "IP address")
        self.ip_label.config(text=self.current_ip, fg=self.text_primary)

        self.country_label = info_row(info_box_inner, "Location")
        self.country_label.config(text=self.current_country, fg=self.text_primary)

        # Config card
        config_card = tk.Frame(left, bg=self.bg_card, highlightbackground=self.border_subtle, highlightthickness=1)
        config_card.pack(fill="x")

        config_inner = tk.Frame(config_card, bg=self.bg_card)
        config_inner.pack(fill="x", padx=self.space_lg, pady=self.space_lg)

        tk.Label(
            config_inner,
            text="CONFIGURATION",
            bg=self.bg_card,
            fg=self.text_tertiary,
            font=self.font_micro,
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            config_inner,
            text="OpenVPN profile",
            bg=self.bg_card,
            fg=self.text_primary,
            font=self.font_h2,
            anchor="w",
        ).pack(anchor="w", pady=(self.space_sm, self.space_sm))

        file_box = tk.Frame(config_inner, bg=self.bg_secondary, highlightbackground=self.border_subtle, highlightthickness=1)
        file_box.pack(fill="x", pady=(0, self.space_md))

        self.file_label = tk.Label(
            file_box,
            text="No configuration loaded",
            bg=self.bg_secondary,
            fg=self.text_secondary,
            font=self.font_base,
            anchor="w",
            padx=self.space_md,
            pady=self.space_md,
        )
        self.file_label.pack(fill="x")

        self.upload_btn = tk.Button(
            config_inner,
            text="Load .ovpn file",
            font=self.font_button,
            bg=self.accent_primary,
            fg="#041018",
            activebackground=self._blend(self.accent_primary, "#FFFFFF", 0.12),
            activeforeground="#041018",
            cursor="hand2",
            padx=18,
            pady=12,
            relief="flat",
            borderwidth=0,
            command=self.upload_file,
        )
        self.upload_btn.pack(fill="x")
        self.add_button_hover(self.upload_btn, self.accent_primary, self._blend(self.accent_primary, "#FFFFFF", 0.16))

        # Download config link
        download_row = tk.Frame(config_inner, bg=self.bg_card)
        download_row.pack(fill="x", pady=(self.space_sm, 0))

        tk.Label(
            download_row,
            text="Download config file?",
            bg=self.bg_card,
            fg=self.text_secondary,
            font=self.font_small,
            anchor="w",
        ).pack(side="left")

        download_btn = tk.Button(
            download_row,
            text="here",
            font=self.font_button_small,
            bg=self.bg_secondary,
            fg=self.accent_primary,
            activebackground=self._blend(self.bg_secondary, "#FFFFFF", 0.10),
            activeforeground=self.accent_primary,
            cursor="hand2",
            padx=10,
            pady=6,
            relief="flat",
            borderwidth=0,
            command=lambda: self._open_url("https://www.vpnjantit.com/free-openvpn"),
        )
        download_btn.pack(side="left", padx=(self.space_sm, 0))
        self.add_button_hover(download_btn, self.bg_secondary, self._blend(self.bg_secondary, "#FFFFFF", 0.12))

        # Killswitch variable (preserve across responsive re-renders)
        if not hasattr(self, "killswitch_var") or self.killswitch_var is None:
            self.killswitch_var = tk.BooleanVar(value=False)

        # Controls card
        controls_card = tk.Frame(right, bg=self.bg_card, highlightbackground=self.border_subtle, highlightthickness=1)
        controls_card.pack(fill="x")

        controls_inner = tk.Frame(controls_card, bg=self.bg_card)
        controls_inner.pack(fill="x", padx=self.space_lg, pady=self.space_lg)

        top_row = tk.Frame(controls_inner, bg=self.bg_card)
        top_row.pack(fill="x")

        tk.Label(
            top_row,
            text="CONTROLS",
            bg=self.bg_card,
            fg=self.text_tertiary,
            font=self.font_micro,
        ).pack(side="left")

        ks_row = tk.Frame(controls_inner, bg=self.bg_card)
        ks_row.pack(fill="x", pady=(self.space_md, self.space_md))
        ks_row.grid_columnconfigure(0, weight=1)
        ks_row.grid_columnconfigure(1, weight=0)

        ks_text = tk.Frame(ks_row, bg=self.bg_card)
        ks_text.grid(row=0, column=0, sticky="w")

        tk.Label(
            ks_text,
            text="Killswitch",
            bg=self.bg_card,
            fg=self.text_primary,
            font=self.font_h3,
        ).pack(anchor="w")

        tk.Label(
            ks_text,
            text="Blocks all traffic outside the VPN tunnel",
            bg=self.bg_card,
            fg=self.text_secondary,
            font=self.font_small,
        ).pack(anchor="w", pady=(2, 0))

        toggle_wrap = tk.Frame(ks_row, bg=self.bg_card)
        if width < 520:
            toggle_wrap.grid(row=1, column=0, sticky="w", pady=(self.space_sm, 0))
        else:
            toggle_wrap.grid(row=0, column=1, sticky="e")

        self.toggle_canvas = tk.Canvas(
            toggle_wrap,
            width=58,
            height=30,
            bg=self.bg_card,
            highlightthickness=0,
            cursor="hand2",
        )
        self.toggle_canvas.pack(side="left")

        # Rounded toggle track
        self._toggle_track_left = self.toggle_canvas.create_oval(4, 6, 24, 26, fill=self.bg_secondary, outline=self.border_strong, width=1)
        self._toggle_track_mid = self.toggle_canvas.create_rectangle(14, 6, 44, 26, fill=self.bg_secondary, outline=self.border_strong, width=1)
        self._toggle_track_right = self.toggle_canvas.create_oval(34, 6, 54, 26, fill=self.bg_secondary, outline=self.border_strong, width=1)

        # Toggle thumb
        self.toggle_circle = self.toggle_canvas.create_oval(6, 8, 22, 24, fill=self.text_tertiary, outline="")

        self.toggle_canvas.bind("<Button-1>", self.toggle_killswitch_click)

        # Buttons
        button_grid = tk.Frame(controls_inner, bg=self.bg_card)
        button_grid.pack(fill="x")
        for i in range(2):
            button_grid.grid_columnconfigure(i, weight=1, uniform="btn")

        def make_btn(parent, text, bg, fg, command):
            btn = tk.Button(
                parent,
                text=text,
                font=self.font_button,
                bg=bg,
                fg=fg,
                activebackground=self._blend(bg, "#FFFFFF", 0.12),
                activeforeground=fg,
                cursor="hand2",
                padx=16,
                pady=12,
                relief="flat",
                borderwidth=0,
                command=command,
            )
            btn.configure(disabledforeground=self._blend(self.text_secondary, self.bg_secondary, 0.4))
            self.add_button_hover(btn, bg, self._blend(bg, "#FFFFFF", 0.14))
            return btn

        self.start_btn = make_btn(button_grid, "Start VPN", self.accent_success, "#041018", self.start_vpn)
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0, self.space_sm), pady=(0, self.space_sm))

        self.force_stop_btn = make_btn(button_grid, "Force stop", self.accent_danger, "#1B0A10", self.force_stop_vpn)
        self.force_stop_btn.grid(row=0, column=1, sticky="ew", padx=(self.space_sm, 0), pady=(0, self.space_sm))

        self.status_btn = make_btn(button_grid, "Status check", self.accent_primary, "#041018", self.check_status)
        self.status_btn.grid(row=1, column=0, sticky="ew", padx=(0, self.space_sm))

        self.restore_btn = make_btn(button_grid, "Restore network", self.accent_secondary, "#12091f", self.restore_network)
        self.restore_btn.grid(row=1, column=1, sticky="ew", padx=(self.space_sm, 0))

        self.close_btn = tk.Button(
            controls_inner,
            text="Exit",
            font=self.font_button,
            bg=self.bg_secondary,
            fg=self.text_primary,
            activebackground=self._blend(self.bg_secondary, "#FFFFFF", 0.08),
            activeforeground=self.text_primary,
            cursor="hand2",
            padx=16,
            pady=12,
            relief="flat",
            borderwidth=0,
            command=self.close_app,
        )
        self.close_btn.pack(fill="x", pady=(self.space_md, 0))
        self.add_button_hover(self.close_btn, self.bg_secondary, self._blend(self.bg_secondary, "#FFFFFF", 0.10))

        # Footer
        footer = tk.Frame(self.scrollable_frame, bg=self.bg_primary)
        footer.pack(fill="x", padx=content_padx, pady=(self.space_lg, self.space_lg))
        tk.Label(
            footer,
            text="© 2025 An0m0s VPN • Built for secure connectivity",
            bg=self.bg_primary,
            fg=self.text_tertiary,
            font=self.font_micro,
            anchor="w",
        ).pack(anchor="w")

        links_row = tk.Frame(footer, bg=self.bg_primary)
        links_row.pack(anchor="w", pady=(self.space_xs, 0))

        tk.Label(
            links_row,
            text="Links:",
            bg=self.bg_primary,
            fg=self.text_tertiary,
            font=self.font_micro,
        ).pack(side="left")

        def make_link_btn(text, url):
            btn = tk.Button(
                links_row,
                text=text,
                font=self.font_button_small,
                bg=self.bg_secondary,
                fg=self.accent_primary,
                activebackground=self._blend(self.bg_secondary, "#FFFFFF", 0.10),
                activeforeground=self.accent_primary,
                cursor="hand2",
                padx=12,
                pady=6,
                relief="flat",
                borderwidth=0,
                command=lambda: self._open_url(url),
            )
            self.add_button_hover(btn, self.bg_secondary, self._blend(self.bg_secondary, "#FFFFFF", 0.12))
            return btn

        make_link_btn("GitHub", "https://github.com/Anasx1111").pack(side="left", padx=(self.space_sm, 0))
        make_link_btn("LinkedIn", "https://www.linkedin.com/in/anas-gharaibeh-9746b72b7/").pack(side="left", padx=(self.space_sm, 0))
        make_link_btn("Instagram", "https://www.instagram.com/anas.gharibeh/").pack(side="left", padx=(self.space_sm, 0))

        # Sync stateful widgets after (re)build
        self._sync_config_label()
        self._sync_toggle_visual()

    def _sync_config_label(self):
        if not hasattr(self, "file_label"):
            return
        if self.ovpn_file:
            filename = os.path.basename(self.ovpn_file)
            self.file_label.config(text=f"Loaded: {filename}", fg=self.accent_success)
        else:
            self.file_label.config(text="No configuration loaded", fg=self.text_secondary)

    def _sync_toggle_visual(self):
        if not hasattr(self, "toggle_canvas"):
            return
        if not hasattr(self, "toggle_circle"):
            return
        if not hasattr(self, "_toggle_track_left"):
            return

        enabled = False
        try:
            enabled = bool(self.killswitch_var.get())
        except Exception:
            enabled = bool(self.killswitch_enabled)

        if enabled:
            for item in (self._toggle_track_left, self._toggle_track_mid, self._toggle_track_right):
                self.toggle_canvas.itemconfig(
                    item,
                    fill=self._blend(self.accent_warning, self.bg_primary, 0.85),
                    outline=self._blend(self.accent_warning, self.bg_primary, 0.55),
                )
            self.toggle_canvas.coords(self.toggle_circle, 36, 8, 52, 24)
            self.toggle_canvas.itemconfig(self.toggle_circle, fill=self.text_primary)
        else:
            for item in (self._toggle_track_left, self._toggle_track_mid, self._toggle_track_right):
                self.toggle_canvas.itemconfig(item, fill=self.bg_secondary, outline=self.border_strong)
            self.toggle_canvas.coords(self.toggle_circle, 6, 8, 22, 24)
            self.toggle_canvas.itemconfig(self.toggle_circle, fill=self.text_tertiary)
    
    def draw_premium_logo(self):
        """Draw animated premium logo"""
        # Draw glowing circle
        self.logo_canvas.create_oval(10, 10, 70, 70, 
                                     outline=self.accent_primary, 
                                     width=3, 
                                     tags="logo")
        # Draw VPN shield icon
        self.logo_canvas.create_polygon(
            40, 20, 55, 30, 55, 50, 40, 60, 25, 50, 25, 30,
            fill=self.accent_primary,
            outline="",
            tags="shield"
        )
        # Lock symbol
        self.logo_canvas.create_rectangle(35, 40, 45, 50, 
                                          fill=self.bg_primary, 
                                          outline="",
                                          tags="lock")
    
    def add_button_hover(self, button, normal_color, hover_color):
        """Add premium hover effect to buttons"""
        def on_enter(e):
            try:
                if str(button.cget("state")) == "disabled":
                    return
            except Exception:
                pass
            button.config(bg=hover_color)
        
        def on_leave(e):
            try:
                if str(button.cget("state")) == "disabled":
                    return
            except Exception:
                pass
            button.config(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def start_animations(self):
        """Start background animations"""
        # Fetch IP info on startup
        self.refresh_ip_info()

        # Subtle pulse on the connection pill to draw attention without being noisy
        self.pulse_status_indicator()
    
    def animate_logo(self):
        """Animate the logo rotation"""
        if self.animation_running:
            self.root.after(50, self.animate_logo)
    
    def pulse_status_indicator(self):
        """Pulse animation for status indicator"""
        if self.animation_running:
            self._pulse_phase = (self._pulse_phase + 1) % 120
            if hasattr(self, "connection_pill"):
                if self.is_running:
                    base = self._blend(self.accent_success, self.bg_primary, 0.80)
                    pulse = self._blend(self.accent_success, "#FFFFFF", 0.12)
                else:
                    base = self._blend(self.bg_secondary, self.bg_primary, 0.35)
                    pulse = self._blend(self.bg_secondary, "#FFFFFF", 0.10)
                t = (1 + math.sin(self._pulse_phase / 120 * 2 * math.pi)) / 2
                bg = self._blend(base, pulse, 0.35 * t)
                self.connection_pill.config(bg=bg)
            self.root.after(60, self.pulse_status_indicator)
    
    def get_ip_info(self):
        """Get IP address and country information"""
        try:
            # Try multiple services for redundancy
            services = [
                'https://ipapi.co/json/',
                'https://ipinfo.io/json'
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract IP and Country based on service
                        if 'ipapi.co' in service:
                            ip = data.get('ip', 'Unknown')
                            country = data.get('country_name', 'Unknown')
                            city = data.get('city', '')
                            if city:
                                country = f"{city}, {country}"
                        elif 'ipinfo.io' in service:
                            ip = data.get('ip', 'Unknown')
                            country = data.get('country', 'Unknown')
                            city = data.get('city', '')
                            if city:
                                country = f"{city}, {country}"
                        
                        return ip, country
                except:
                    continue
            
            return "Unable to fetch", "Unknown"
        except Exception as e:
            return "Error", "Unknown"
    
    def refresh_ip_info(self):
        """Refresh IP and country information in a separate thread"""
        def fetch_and_update():
            # Update UI to show loading
            self.root.after(0, lambda: self.ip_label.config(text="Loading…", fg=self.accent_warning))
            self.root.after(0, lambda: self.country_label.config(text="Loading…", fg=self.accent_warning))
            
            # Fetch IP info
            ip, country = self.get_ip_info()
            
            # Update variables
            self.current_ip = ip
            self.current_country = country
            
            # Update UI
            self.root.after(0, lambda: self.ip_label.config(text=ip, fg=self.text_primary))
            self.root.after(0, lambda: self.country_label.config(text=country, fg=self.text_primary))
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=fetch_and_update, daemon=True).start()
    
    def upload_file(self):
        """Handle file upload with premium feedback"""
        file_path = filedialog.askopenfilename(
            title="Select OpenVPN configuration file",
            filetypes=[("OpenVPN Files", "*.ovpn"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.ovpn_file = file_path
            self._sync_config_label()
            filename = os.path.basename(file_path)
            messagebox.showinfo("Success", f"Configuration loaded successfully.\n\n{filename}")
    
    def toggle_killswitch_click(self, event=None):
        """Handle toggle switch click with animation and actual killswitch control"""
        # Toggle the state
        current_state = self.killswitch_var.get()
        new_state = not current_state
        
        # If enabling killswitch
        if new_state:
            # Check if VPN config is loaded
            if not self.ovpn_file:
                messagebox.showwarning(
                    "Warning",
                    "Load a VPN configuration file first.\n\nThe killswitch needs VPN server details."
                )
                return
            
            # Ask for confirmation
            response = messagebox.askyesno(
                "Enable killswitch",
                "This will block all internet traffic except:\n" +
                "  • VPN tunnel (tun/tap)\n" +
                "  • VPN server connection\n" +
                "  • Localhost\n\n" +
                "If the VPN disconnects, you may have no internet.\n\nContinue?"
            )
            
            if not response:
                return
            
            # Apply killswitch
            if self.apply_killswitch():
                self.killswitch_var.set(True)
                self._sync_toggle_visual()
                messagebox.showinfo(
                    "Success",
                    "Killswitch enabled.\n\nInternet is now blocked except VPN traffic.\nStart the VPN to restore access through the tunnel."
                )
            else:
                messagebox.showerror("Error", "Failed to enable killswitch.")
        
        # If disabling killswitch
        else:
            # Ask for confirmation
            response = messagebox.askyesno(
                "Disable Killswitch",
                "Killswitch is currently active.\n\nInternet is blocked except VPN traffic.\n\nDisable it and restore normal internet?"
            )
            
            if not response:
                return
            
            # Remove killswitch
            if self.remove_killswitch():
                self.killswitch_var.set(False)
                self._sync_toggle_visual()
                messagebox.showinfo("Success", "Killswitch disabled.\nInternet restored to normal.")
            else:
                messagebox.showerror("Error", "Failed to disable killswitch.")
    
    def toggle_killswitch(self):
        """Toggle killswitch on/off (legacy support)"""
        pass
    
    def start_vpn(self):
        """Start OpenVPN connection"""
        if not self.ovpn_file:
            messagebox.showerror("Error", "Please upload a .ovpn file first!")
            return
        
        if self.is_running:
            messagebox.showwarning("Warning", "VPN is already running!")
            return
        
        if not os.path.exists(self.ovpn_file):
            messagebox.showerror("Error", "Configuration file not found!")
            return
        
        try:
            # Apply killswitch if enabled (before starting VPN)
            if self.killswitch_var.get() and not self.killswitch_enabled:
                if not self.apply_killswitch():
                    messagebox.showerror("Error", "Failed to apply killswitch!\nVPN start cancelled.")
                    return
                time.sleep(1)
            
            # Start OpenVPN (already running as root)
            cmd = ['openvpn', '--config', self.ovpn_file]
            
            self.vpn_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Get the PID
            time.sleep(1)
            result = subprocess.run(['pgrep', '-x', 'openvpn'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.vpn_pid = result.stdout.strip().split()[0]
            
            self.is_running = True
            self.update_status()
            messagebox.showinfo("Success", "VPN started successfully!")
            
            # Start monitoring thread
            threading.Thread(target=self.monitor_vpn, daemon=True).start()
            
            # Wait a bit for VPN to establish, then refresh IP
            time.sleep(3)
            self.refresh_ip_info()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start VPN:\n{str(e)}")
            self.is_running = False
            self.update_status()
    
    def check_status(self):
        """Check VPN status"""
        try:
            # Check if OpenVPN process is running
            result = subprocess.run(
                ['pgrep', '-x', 'openvpn'],
                capture_output=True,
                text=True
            )
            
            status_msg = "=== VPN STATUS CHECK ===\n\n"
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                status_msg += f"✓ OpenVPN Process: RUNNING\n"
                status_msg += f"  PIDs: {', '.join(pids)}\n\n"
                
                # Check network interfaces
                ip_result = subprocess.run(
                    ['ip', 'addr', 'show', 'tun0'],
                    capture_output=True,
                    text=True
                )
                
                if ip_result.returncode == 0:
                    # Extract IP from output
                    lines = ip_result.stdout.split('\n')
                    ip_info = [l.strip() for l in lines if 'inet' in l]
                    
                    status_msg += "✓ VPN Tunnel: ACTIVE\n"
                    status_msg += "  Interface: tun0\n"
                    if ip_info:
                        status_msg += f"  {ip_info[0]}\n\n"
                    
                    status_msg += "Status: CONNECTED ✓"
                    
                    # Update internal state
                    if not self.is_running:
                        self.is_running = True
                        self.update_status()
                    
                    messagebox.showinfo("VPN Status", status_msg)
                else:
                    status_msg += "⚠ VPN Tunnel: NOT FOUND\n"
                    status_msg += "  Interface tun0 not detected\n\n"
                    status_msg += "Status: CONNECTING or FAILED"
                    
                    messagebox.showwarning("VPN Status", status_msg)
            else:
                status_msg += "✗ OpenVPN Process: NOT RUNNING\n\n"
                status_msg += "Status: DISCONNECTED ✗"
                
                # Update internal state
                if self.is_running:
                    self.is_running = False
                    self.vpn_process = None
                    self.vpn_pid = None
                    self.update_status()
                
                messagebox.showinfo("VPN Status", status_msg)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check status:\n{str(e)}")
    
    def monitor_vpn(self):
        """Monitor VPN process in background"""
        while self.is_running:
            if self.vpn_process and self.vpn_process.poll() is not None:
                self.is_running = False
                self.root.after(0, self.update_status)
                break
            time.sleep(2)
    
    def update_status(self):
        """Update premium status indicator with glow effect"""
        if self.is_running:
            # Update button states
            self.start_btn.config(state="disabled", bg=self._blend(self.bg_secondary, self.bg_primary, 0.10))
            self.force_stop_btn.config(state="normal", bg=self.accent_danger)
            if hasattr(self, "connection_pill"):
                self.connection_pill.config(text="CONNECTED", fg=self.text_primary)
        else:
            # Update button states
            self.start_btn.config(state="normal", bg=self.accent_success)
            self.force_stop_btn.config(state="disabled", bg=self._blend(self.bg_secondary, self.bg_primary, 0.10))
            if hasattr(self, "connection_pill"):
                self.connection_pill.config(text="DISCONNECTED", fg=self.text_secondary)
    
    def apply_killswitch(self):
        """Apply firewall rules to block all traffic except VPN"""
        try:
            # Check if we have root privileges
            if os.geteuid() != 0:
                messagebox.showerror("Error", "App must run with root privileges!\nRestart with: pkexec python3 an0m0s_vpn.py")
                return False
            
            # Get current default gateway and interface
            try:
                route_output = subprocess.run(['ip', 'route', 'show', 'default'], 
                                            capture_output=True, text=True, timeout=5)
                default_iface = None
                default_gateway = None
                
                if route_output.returncode == 0 and route_output.stdout:
                    # Parse: default via 192.168.1.1 dev eth0
                    parts = route_output.stdout.split()
                    if 'via' in parts:
                        default_gateway = parts[parts.index('via') + 1]
                    if 'dev' in parts:
                        default_iface = parts[parts.index('dev') + 1]
            except Exception as e:
                default_iface = None
                default_gateway = None
            
            # Get VPN server from config file
            vpn_servers = []
            vpn_ports = []
            if self.ovpn_file and os.path.exists(self.ovpn_file):
                try:
                    with open(self.ovpn_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith('remote '):
                                parts = line.split()
                                if len(parts) >= 2:
                                    vpn_servers.append(parts[1])
                                if len(parts) >= 3:
                                    try:
                                        vpn_ports.append(int(parts[2]))
                                    except:
                                        pass
                            elif line.startswith('port '):
                                parts = line.split()
                                if len(parts) >= 2:
                                    try:
                                        vpn_ports.append(int(parts[1]))
                                    except:
                                        pass
                except Exception as e:
                    pass
            
            # Default VPN ports if none found
            if not vpn_ports:
                vpn_ports = [1194, 443]

            def is_safe_iface(value: str) -> bool:
                if not value:
                    return False
                # Linux ifname max length is typically 15 chars, but allow slightly more
                if len(value) > 32:
                    return False
                return bool(re.fullmatch(r"[A-Za-z0-9_.:+-]+", value))

            def normalize_ports(ports):
                normalized = []
                for port in ports:
                    try:
                        p = int(port)
                    except Exception:
                        continue
                    if 1 <= p <= 65535 and p not in normalized:
                        normalized.append(p)
                return normalized

            def normalize_servers(servers):
                normalized = []
                for server in servers:
                    if not server:
                        continue
                    s = str(server).strip()
                    # Keep as a single token; iptables will reject invalid values.
                    # This avoids command injection by never using a shell.
                    if len(s) > 255:
                        continue
                    if s not in normalized:
                        normalized.append(s)
                return normalized

            def run_cmd(argv, timeout=10, ignore_errors=False, stdin=None, stdout=None):
                try:
                    cp = subprocess.run(
                        argv,
                        capture_output=(stdout is None and stdin is None),
                        text=True,
                        timeout=timeout,
                        stdin=stdin,
                        stdout=stdout,
                    )
                    if cp.returncode != 0 and not ignore_errors:
                        return False
                    return True
                except FileNotFoundError:
                    return False if not ignore_errors else True
                except Exception:
                    return False if not ignore_errors else True

            vpn_ports = normalize_ports(vpn_ports)
            vpn_servers = normalize_servers(vpn_servers)

            if default_iface and not is_safe_iface(default_iface):
                default_iface = None
            
            # Ensure iptables binaries exist
            if shutil.which("iptables") is None:
                messagebox.showerror("Error", "iptables not found on this system.")
                return False

            # Step 1: Backup current rules (best-effort)
            try:
                backup_dir = "/run" if os.path.isdir("/run") and os.access("/run", os.W_OK) else "/tmp"
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    prefix="an0m0s_iptables_",
                    suffix=".rules",
                    dir=backup_dir,
                    delete=False,
                ) as fp:
                    self._iptables_backup_path = fp.name
                try:
                    os.chmod(self._iptables_backup_path, 0o600)
                except Exception:
                    pass
                with open(self._iptables_backup_path, "wb") as out_fp:
                    run_cmd(["iptables-save"], timeout=10, ignore_errors=True, stdout=out_fp)
            except Exception:
                self._iptables_backup_path = None

            # Step 2: Flush existing rules
            commands = [
                ["iptables", "-F"],
                ["iptables", "-X"],
                ["iptables", "-t", "nat", "-F"],
                ["iptables", "-t", "nat", "-X"],
                ["iptables", "-t", "mangle", "-F"],
                ["iptables", "-t", "mangle", "-X"],
            ]
            failed = 0
            for argv in commands:
                if not run_cmd(argv, timeout=10, ignore_errors=True):
                    failed += 1

            # Step 3: Set ACCEPT policies first (avoid lockout)
            for argv in (
                ["iptables", "-P", "INPUT", "ACCEPT"],
                ["iptables", "-P", "OUTPUT", "ACCEPT"],
                ["iptables", "-P", "FORWARD", "ACCEPT"],
            ):
                if not run_cmd(argv, timeout=10, ignore_errors=False):
                    failed += 1

            # Step 4: Allow loopback
            for argv in (
                ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
            ):
                if not run_cmd(argv, timeout=10, ignore_errors=False):
                    failed += 1

            # Step 5: Allow established connections
            for argv in (
                ["iptables", "-A", "INPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
            ):
                if not run_cmd(argv, timeout=10, ignore_errors=False):
                    failed += 1

            # Step 6: Allow VPN tunnel
            for argv in (
                ["iptables", "-A", "INPUT", "-i", "tun+", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-o", "tun+", "-j", "ACCEPT"],
                ["iptables", "-A", "INPUT", "-i", "tap+", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-o", "tap+", "-j", "ACCEPT"],
            ):
                if not run_cmd(argv, timeout=10, ignore_errors=False):
                    failed += 1

            # Step 7: Allow DNS (before VPN connects)
            if default_iface:
                for argv in (
                    ["iptables", "-A", "OUTPUT", "-o", default_iface, "-p", "udp", "--dport", "53", "-j", "ACCEPT"],
                    ["iptables", "-A", "INPUT", "-i", default_iface, "-p", "udp", "--sport", "53", "-j", "ACCEPT"],
                ):
                    if not run_cmd(argv, timeout=10, ignore_errors=False):
                        failed += 1

            # Step 8: Allow DHCP
            if default_iface:
                for argv in (
                    ["iptables", "-A", "OUTPUT", "-o", default_iface, "-p", "udp", "--dport", "67:68", "-j", "ACCEPT"],
                    ["iptables", "-A", "INPUT", "-i", default_iface, "-p", "udp", "--sport", "67:68", "-j", "ACCEPT"],
                ):
                    if not run_cmd(argv, timeout=10, ignore_errors=False):
                        failed += 1

            # Step 9: Allow VPN server connections
            if default_iface:
                if vpn_servers:
                    for server in vpn_servers:
                        for port in vpn_ports:
                            for proto in ("udp", "tcp"):
                                argv = [
                                    "iptables",
                                    "-A",
                                    "OUTPUT",
                                    "-o",
                                    default_iface,
                                    "-d",
                                    server,
                                    "-p",
                                    proto,
                                    "--dport",
                                    str(port),
                                    "-j",
                                    "ACCEPT",
                                ]
                                if not run_cmd(argv, timeout=10, ignore_errors=False):
                                    failed += 1
                        argv_in = ["iptables", "-A", "INPUT", "-i", default_iface, "-s", server, "-j", "ACCEPT"]
                        if not run_cmd(argv_in, timeout=10, ignore_errors=False):
                            failed += 1
                else:
                    for port in vpn_ports:
                        for proto in ("udp", "tcp"):
                            argv = [
                                "iptables",
                                "-A",
                                "OUTPUT",
                                "-o",
                                default_iface,
                                "-p",
                                proto,
                                "--dport",
                                str(port),
                                "-j",
                                "ACCEPT",
                            ]
                            if not run_cmd(argv, timeout=10, ignore_errors=False):
                                failed += 1

            # Step 10: Allow gateway
            if default_gateway and default_iface:
                for argv in (
                    ["iptables", "-A", "OUTPUT", "-o", default_iface, "-d", default_gateway, "-j", "ACCEPT"],
                    ["iptables", "-A", "INPUT", "-i", default_iface, "-s", default_gateway, "-j", "ACCEPT"],
                ):
                    if not run_cmd(argv, timeout=10, ignore_errors=False):
                        failed += 1

            # Step 11: Drop all other traffic on physical interface
            if default_iface:
                for argv in (
                    ["iptables", "-A", "OUTPUT", "-o", default_iface, "-j", "DROP"],
                    ["iptables", "-A", "INPUT", "-i", default_iface, "-j", "DROP"],
                ):
                    if not run_cmd(argv, timeout=10, ignore_errors=False):
                        failed += 1

            # Step 12: Block IPv6 (best-effort)
            for argv in (
                ["ip6tables", "-P", "INPUT", "DROP"],
                ["ip6tables", "-P", "OUTPUT", "DROP"],
                ["ip6tables", "-P", "FORWARD", "DROP"],
            ):
                run_cmd(argv, timeout=10, ignore_errors=True)

            # If too many failures, consider it unsuccessful
            total_ops = 1 + 6 + 3 + 2 + 2 + 4
            if failed > max(5, total_ops // 2):
                return False
            
            self.killswitch_enabled = True
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Killswitch failed:\n{str(e)}")
            return False
    
    def remove_killswitch(self):
        """Remove killswitch and restore normal network"""
        try:
            # Check if we have root privileges
            if os.geteuid() != 0:
                messagebox.showerror("Error", "App must run with root privileges!")
                return False
            
            def run_cmd(argv, timeout=10, ignore_errors=False, stdin=None):
                try:
                    cp = subprocess.run(
                        argv,
                        capture_output=(stdin is None),
                        text=True,
                        timeout=timeout,
                        stdin=stdin,
                    )
                    if cp.returncode != 0 and not ignore_errors:
                        return False
                    return True
                except FileNotFoundError:
                    return False if not ignore_errors else True
                except Exception:
                    return False if not ignore_errors else True

            # Best-effort restore from backup created when enabling killswitch
            restored = False
            if self._iptables_backup_path and os.path.exists(self._iptables_backup_path):
                try:
                    st = os.stat(self._iptables_backup_path)
                    # Require root-owned and not world/group readable
                    if st.st_uid == 0 and (st.st_mode & 0o077) == 0:
                        if shutil.which("iptables-restore") is not None:
                            with open(self._iptables_backup_path, "rb") as fp:
                                restored = run_cmd(["iptables-restore"], timeout=15, ignore_errors=False, stdin=fp)
                except Exception:
                    restored = False

            if restored:
                try:
                    os.remove(self._iptables_backup_path)
                except Exception:
                    pass
                self._iptables_backup_path = None
            else:
                # Fallback: restore normal internet by flushing and setting ACCEPT policies
                commands = [
                    ["iptables", "-P", "INPUT", "ACCEPT"],
                    ["iptables", "-P", "OUTPUT", "ACCEPT"],
                    ["iptables", "-P", "FORWARD", "ACCEPT"],
                    ["iptables", "-F"],
                    ["iptables", "-X"],
                    ["iptables", "-t", "nat", "-F"],
                    ["iptables", "-t", "nat", "-X"],
                    ["iptables", "-t", "mangle", "-F"],
                    ["iptables", "-t", "mangle", "-X"],
                    ["ip6tables", "-P", "INPUT", "ACCEPT"],
                    ["ip6tables", "-P", "OUTPUT", "ACCEPT"],
                    ["ip6tables", "-P", "FORWARD", "ACCEPT"],
                    ["ip6tables", "-F"],
                ]
                failed = 0
                for argv in commands:
                    if not run_cmd(argv, timeout=10, ignore_errors=True):
                        failed += 1
                if failed > len(commands) / 2:
                    return False
            
            self.killswitch_enabled = False
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore:\n{str(e)}")
            return False
    
    def force_stop_vpn(self):
        """Force stop VPN using direct sudo commands"""
        response = messagebox.askyesno(
            "Force Stop",
            "This will forcefully kill all OpenVPN processes.\n\nContinue?"
        )
        
        if not response:
            return
        
        try:
            # Direct force kill (already running as root)
            commands = [
                ['killall', '-9', 'openvpn'],
                ['pkill', '-9', '-f', 'openvpn']
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, 
                                          text=True, timeout=5)
                except Exception as e:
                    pass
            
            time.sleep(2)
            
            # Check if stopped
            check = subprocess.run(['pgrep', '-x', 'openvpn'], 
                                  capture_output=True, text=True)
            
            if check.returncode == 0:
                messagebox.showerror(
                    "Failed",
                    "Force stop failed!\nOpenVPN still running.\n\nTry in terminal:\nsudo killall -9 openvpn"
                )
            else:
                self.is_running = False
                self.vpn_process = None
                self.vpn_pid = None
                
                # Don't touch killswitch - let user control it manually via toggle
                if self.killswitch_enabled:
                    messagebox.showinfo(
                        "✓ VPN Stopped",
                        "VPN force stopped successfully!\n\n" +
                        "⚠ WARNING: Killswitch is still ACTIVE\n" +
                        "Internet is blocked. Use the toggle to disable it."
                    )
                else:
                    self.update_status()
                    messagebox.showinfo("Success", "VPN force stopped successfully!")
                
                self.update_status()
                # Refresh IP info after stopping VPN
                time.sleep(2)
                self.refresh_ip_info()
                
        except Exception as e:
            messagebox.showerror("Error", f"Force stop failed:\n{str(e)}")
    
    def restore_network(self):
        """Restore network to normal (remove all iptables rules)"""
        response = messagebox.askyesno(
            "Restore Network",
            "This will remove all firewall rules and restore normal internet.\nContinue?"
        )
        if response:
            if self.remove_killswitch():
                messagebox.showinfo("Success", "Network restored to normal!")
            else:
                messagebox.showerror("Error", "Failed to restore network!")
    
    def close_app(self):
        """Close application with cleanup"""
        self.animation_running = False  # Stop animations
        
        # Unbind mouse wheel events
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        except:
            pass
        
        if self.is_running:
            response = messagebox.askyesno(
                "Confirm exit",
                "VPN is still running. Force stop it and exit?"
            )
            if response:
                # Force stop without asking again
                try:
                    commands = [
                        ['killall', '-9', 'openvpn'],
                        ['pkill', '-9', '-f', 'openvpn']
                    ]
                    for cmd in commands:
                        try:
                            subprocess.run(cmd, capture_output=True, timeout=5)
                        except:
                            pass
                    self.is_running = False
                    
                    # Check killswitch before closing
                    if self.killswitch_enabled:
                        ks_response = messagebox.askyesno(
                            "Killswitch still active",
                            "Killswitch is active — internet is blocked outside the VPN.\n\n" +
                            "Disable killswitch before closing?\n\n" +
                            "• Yes: disable and restore internet\n" +
                            "• No: keep killswitch active"
                        )
                        if ks_response:
                            self.remove_killswitch()
                            # Update toggle visual
                            self.killswitch_var.set(False)
                            self.toggle_canvas.itemconfig(self.toggle_bg,
                                                         fill=self.bg_secondary,
                                                         outline=self.text_secondary)
                            self.toggle_canvas.coords(self.toggle_circle, 8, 8, 28, 22)
                            self.toggle_canvas.itemconfig(self.toggle_circle, fill=self.text_secondary)
                except:
                    pass
                time.sleep(1)
                self.root.quit()
        else:
            # Check if killswitch is active
            if self.killswitch_enabled:
                response = messagebox.askyesno(
                    "Killswitch active",
                    "Killswitch is still active. Disable it before closing?"
                )
                if response:
                    self.remove_killswitch()
            self.root.quit()


def main():
    # Check and get root privileges first
    check_root()
    
    # Verify we actually have root
    if os.geteuid() != 0:
        sys.exit(1)
    
    # Now run the application with root privileges
    root = tk.Tk()
    app = An0m0sVPN(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()


if __name__ == "__main__":
    main()
