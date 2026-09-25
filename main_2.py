# Build with:
# pyinstaller --onefile --name autocharts main.py

import configparser
import time
from pathlib import Path
import shutil
from PIL import Image
from briefing_to_kneeboard import build_pdf
import subprocess
import ctypes
from ctypes import wintypes

# TODO: Prüfen, ob die AudioDeviceCmdlets installiert sind. Wenn nicht, installieren
# TODO: Einlesen der IDs ueber .ini
HEADSET_OUT = "{0.0.0.00000000}.{cb14d36f-b009-486d-80da-969a87686254}"
HEADSET_IN = "{0.0.1.00000000}.{c3432b0a-73bf-4f2d-8c31-b2d47104ebf9}"
VR_OUT = "{0.0.0.00000000}.{5ebc4a12-f53a-4d1e-83a6-e1d95d30b2ae}"
VR_IN = "{0.0.1.00000000}.{d60d42cf-e196-42d4-b943-30a876d76bef}"
WM_HOTKEY = 0x0312
HOTKEY_ID = 1
VK_F4 = 0x73

def searchbriefing():
    global mode
    mode = "parsing"
    print(mode + " ...\n")
    chartspraesent = ['', '']

    with open(briefingfile, "r", encoding="cp1252", errors="replace") as f:
        for zeile in f:
            wortliste = zeile.split()

            if len(wortliste) >= 3:
                if wortliste[0] == "Dep":
                    if wortliste[1] == "Ground:":
                        departure = wortliste[2]
                        changecharts("departure", departure)
                        chartspraesent[0] = departure
                elif wortliste[0] == "Arr":
                    if wortliste[1] == "Ground:":
                        arrival = wortliste[2]
                        if arrival not in chartspraesent:
                            changecharts("arrival", arrival)
                            chartspraesent[1] = arrival
                elif wortliste[0] == "Alt":
                    if wortliste[1] == "Ground:":
                        alternate = wortliste[2]
                        if alternate not in chartspraesent:
                            changecharts("alternate", alternate)

    if theater == "korea":
        datachartzerlegen(falcon_main + 'Data\\TerrData\\Objects\\KoreaObj\\7997.dds')
    elif theater == "balkan":
        datachartzerlegen(falcon_main + 'Data\\Add-On Balkans\\Terrdata\\objects\\KoreaObj\\7997.dds')

    try:
        build_pdf(
            briefing,
            okb_kneeboard + 'briefing.pdf',
        )

    except Exception as exc:

        print()
        print("Fehler beim Erstellen der Briefingdatei")
        print(exc)
        print()


def changecharts(agency, town):
    global mode
    global theater
    mode = "change charts"
    print(mode + ' ' + agency + ' to ' + town + '\n')
    portlaenge = len(town) + 1

    for port in airports:
        if port.name == town or port.name.startswith(town + " "):
            if agency == "departure":
                clear_directory(okb_departure)
                copy_recursive(charts / port, okb_departure)
                theater = port.parts[0]
                print(theater)
            elif agency == "arrival":
                clear_directory(okb_arrival)
                copy_recursive(charts / port, okb_arrival)
            elif agency == "alternate":
                clear_directory(okb_alternate)
                copy_recursive(charts / port, okb_alternate)


def list_directories(root_dir):
    root = Path(root_dir)
    return [p.relative_to(root) for p in root.rglob("*") if p.is_dir()]


def clear_directory(directory):
    """Löscht alle Inhalte im Verzeichnis, behält aber das Verzeichnis selbst."""
    directory = Path(directory)
    for item in sorted(directory.rglob("*"), reverse=True):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            item.rmdir()


def copy_recursive(src, dst):
    """
    Kopiert alle Dateien und Unterverzeichnisse von src nach dst.
    src und dst sollten Path-Objekte oder Strings sein.
    """
    src = Path(src)
    dst = Path(dst)

    for item in src.rglob("*"):
        target = dst / item.relative_to(src)
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            shutil.copy2(item, target)


def datachartzerlegen(dds_path):
    global mode
    mode = "creating datacard"
    print(mode + " ...\n")
    """
    Liest eine DDS-Datei, teilt sie horizontal in zwei Hälften,
    skaliert jede Hälfte in der Breite um Faktor 1.2 und speichert als PNG.

    :param dds_path: Pfad zur DDS-Datei
    :param output_prefix: Präfix für die Ausgabedateien
    """
    # DDS einlesen
    im = Image.open(dds_path)
    width, height = im.size
    half_width = width // 2

    # Hälften ausschneiden
    left_half = im.crop((0, 0, half_width, height))
    right_half = im.crop((half_width, 0, width, height))

    halves = [left_half, right_half]

    # Breite skalieren (Faktor 1.2)
    scaled_halves = []
    for i, tile in enumerate(halves):
        new_width = int(tile.width * 1.2)
        new_height = tile.height  # Höhe bleibt gleich
        scaled = tile.resize((new_width, new_height), Image.LANCZOS)
        scaled_halves.append(scaled)

        # Als PNG speichern
        if i == 0:
            datei = 'links'
        else:
            datei = 'rechts'
        output_path = okb_datacard + f"{datei}.png"
        scaled.save(output_path)
        print(f"Gespeichert: {output_path}\n")


def kill_all_instances(name):
    """Alle Instanzen eines Prozesses beenden und warten, bis keine mehr laufen."""
    try:
        # Versucht alle Instanzen zu beenden (/F = erzwingen, /IM = nach Name)
        subprocess.run(["taskkill", "/F", "/IM", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Fehler beim Beenden von {name}: {e}")

    # Sicherstellen, dass wirklich nichts mehr läuft
    while True:
        try:
            output = subprocess.check_output(["tasklist", "/FI", f"IMAGENAME eq {name}"], text=True)
            if name.lower() not in output.lower():
                break  # Prozess ist weg
        except subprocess.CalledProcessError:
            break
        time.sleep(0.2)


def start_process(path):
    """Startet den Prozess neu."""
    print(f"Starte {path} ...")
    return subprocess.Popen([path])


def check_audio_devices():
    ps = """
    Import-Module AudioDeviceCmdlets

    Get-AudioDevice -List | ForEach-Object {
        "$($_.ID)|$($_.Name)|$($_.Type)"
    }
    """

    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            ps,
        ],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "AudioDeviceCmdlets konnte nicht geladen werden:\n" + result.stderr.strip()
        )

    devices = {}

    for line in result.stdout.splitlines():
        parts = line.split("|", 2)

        if len(parts) == 3:
            device_id, name, device_type = parts
            devices[device_id] = (name, device_type)

    expected = [
        ("Headset Output", HEADSET_OUT, "Playback"),
        ("Headset Input", HEADSET_IN, "Recording"),
        ("VR Output", VR_OUT, "Playback"),
        ("VR Input", VR_IN, "Recording"),
    ]

    print("Audio-Geräte:")
    missing = False

    for label, device_id, expected_type in expected:
        device = devices.get(device_id)

        if device is None:
            print(f"  ✗ {label}")
            missing = True
        elif device[1] != expected_type:
            print(f"  ✗ {label} (falscher Typ: {device[1]})")
            missing = True
        else:
            print(f"  ✓ {label}: {device[0]}")

    if missing:
        raise RuntimeError("Mindestens ein benötigtes Audio-Gerät fehlt.")

    print("Audio-Geräte: OK\n")


def toggle_audio():
    ps = f"""
    Add-Type -AssemblyName System.Speech
    Import-Module AudioDeviceCmdlets

    $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer

    $current = (Get-AudioDevice -Playback).ID

    if ($current -eq '{VR_OUT}') {{
        $target = 'Headset'
        $output = '{HEADSET_OUT}'
        $input  = '{HEADSET_IN}'
    }}
    else {{
        $target = 'VR'
        $output = '{VR_OUT}'
        $input  = '{VR_IN}'
    }}

    $speaker.Speak("Audio output switching to $target")

    Set-AudioDevice -ID $output -DefaultOnly
    Set-AudioDevice -ID $input -DefaultOnly

    $speaker.Speak("Audio output switched to $target")
    """

    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            ps
        ],
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('autocharts.ini')
    falcon_main = config['Directories']['Falcon_main']
    charts = config['Directories']['Charts']
    okb_main = config['Directories']['OpenKneeboard_main']
    okb_exe = 'OpenKneeboardApp.exe'
    okb = okb_main + okb_exe
    okb_kneeboard = config['Directories']['OKB_Knee']
    okb_departure = okb_kneeboard + "departure\\"
    okb_arrival = okb_kneeboard + "arrival\\"
    okb_alternate = okb_kneeboard + "alternate\\"
    okb_datacard = okb_kneeboard + "wdp\\"
    briefing = falcon_main + "User\\Briefings\\briefing.txt"
    briefingfile = Path(briefing)
    airports = list_directories(Path(charts))

    # print(airports)

    mode = "parsing charts"
    lastchangedate = briefingfile.stat().st_mtime
    # lastchangedate = watchfile.stat().st_mtime
    theater = "korea"
    # print(lastchangedate)

    # Initialisierung der Standard Ein- Ausgabegeraete Umschaltung
    user32 = ctypes.windll.user32
    if not user32.RegisterHotKey(None, HOTKEY_ID, 0, VK_F4):
        raise RuntimeError("F4 konnte nicht registriert werden")
    print("F4 Hotkey registriert")
    check_audio_devices()

    while True:
        msg = wintypes.MSG()

        # Polling for Hotkeys
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                # Bei F4: Standard Ein- und Ausgabegeraete umschalten
                toggle_audio()

        # Ueberwachen der Briefing Datei
        if mode != "watching":
            mode = "watching"
            print(mode + " ...\n")
        newchangedate = briefingfile.stat().st_mtime
        # Bei Aenderung:
        # Charts in Openkneemap aktualisieren
        # Briefing in Openkneemap aktualisieren
        # WDP in Openkneemap aktualisieren
        if newchangedate != lastchangedate:
            kill_all_instances(okb_exe)
            searchbriefing()
            lastchangedate = newchangedate
            start_process(okb)
            print('changed\n')
        time.sleep(1)
