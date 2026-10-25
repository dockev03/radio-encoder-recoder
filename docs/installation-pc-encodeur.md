# Installation du PC encodeur

Procédure complète pour préparer, de zéro, le PC encodeur de Vichy Radio.
Ce poste est un **prérequis** au dashboard : en mode PROD, l'outil ne fait que surveiller et enregistrer une chaîne audio qui doit déjà fonctionner.

> Les valeurs entre `<chevrons>` (IP, utilisateur, serveur AzuraCast…) sont à adapter.
> **Aucun mot de passe ne doit être recopié dans ce dépôt.**

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Matériel](#2-matériel)
3. [Système d'exploitation](#3-système-dexploitation)
4. [Réseau et heure](#4-réseau-et-heure)
5. [Paquets](#5-paquets)
6. [Carte son Aureon et PipeWire](#6-carte-son-aureon-et-pipewire)
7. [EasyEffects](#7-easyeffects)
8. [BUTT et AzuraCast](#8-butt-et-azuracast)
9. [Énergie et démarrage automatique](#9-énergie-et-démarrage-automatique)
10. [Dashboard](#10-dashboard)
11. [Watchdog audio](#11-watchdog-audio)
12. [Pare-feu](#12-pare-feu)
13. [Recette finale](#13-recette-finale)
14. [Dépannage](#14-dépannage)

---

## 1. Vue d'ensemble

```
Table de mixage ─► Aureon 5.1 MkII (USB) ─► PipeWire ─► EasyEffects ─► easyeffects_source
                                                                         ├─► BUTT ─► AzuraCast
                                                                         ├─► pw-cat (VU-mètre du dashboard)
                                                                         └─► FFmpeg (enregistrements du dashboard)
```

Le dashboard dépend de quatre points :

| Le dashboard vérifie… | Par… | Section |
|---|---|---|
| la présence de l'Aureon | `lsusb`, identifiant `0ccd:0028` | [6](#6-carte-son-aureon-et-pipewire) |
| qu'EasyEffects tourne | `pgrep -x easyeffects` | [7](#7-easyeffects) |
| la source `easyeffects_source` (48 kHz, stéréo) | `pactl`, `pw-cat`, FFmpeg | [7](#7-easyeffects) |
| que BUTT tourne | `pgrep -x butt` | [8](#8-butt-et-azuracast) |

## 2. Matériel

- PC x86_64, 4 Go de RAM minimum, SSD.
- Carte son **TerraTec Aureon 5.1 MkII** (USB), branchée **directement** sur le PC, sans hub.
- Câble entre la sortie de la table de mixage et l'entrée ligne de l'Aureon.
- Liaison réseau **filaire** vers la régie et Internet.
- Optionnel : disque ou clé USB pour stocker les enregistrements (monté sous `/media` ou `/mnt`).

## 3. Système d'exploitation

**Distribution recommandée : Debian 13 (Trixie)**. Elle fournit d'origine Python 3.13, PipeWire, EasyEffects et BUTT.

À l'installation :

- choisir un **environnement de bureau** (GNOME ou XFCE) : EasyEffects et BUTT sont des applications graphiques ;
- créer un utilisateur dédié, par exemple `<encodeur>`, qui fera tourner toute la chaîne ;
- installer le **serveur SSH** pour l'administration à distance.

Activer la **connexion automatique** de cet utilisateur : EasyEffects et BUTT ont besoin d'une session graphique ouverte.

- GNOME (GDM) : dans `/etc/gdm3/daemon.conf`, section `[daemon]` :
  ```ini
  AutomaticLoginEnable=true
  AutomaticLogin=<encodeur>
  ```
- XFCE (LightDM) : dans `/etc/lightdm/lightdm.conf`, section `[Seat:*]` : `autologin-user=<encodeur>`.

## 4. Réseau et heure

- **IP fixe** : de préférence une réservation DHCP sur la box ou le routeur. Sinon :
  ```bash
  nmcli con show                                  # repérer le nom de la connexion
  sudo nmcli con mod "<connexion>" ipv4.method manual \
    ipv4.addresses <192.168.1.50/24> ipv4.gateway <192.168.1.1> ipv4.dns <192.168.1.1>
  sudo nmcli con up "<connexion>"
  ```
- **Nom d'hôte** : `sudo hostnamectl set-hostname <vichy-encodeur>`
- **Heure** : l'horodatage des enregistrements en dépend.
  ```bash
  sudo timedatectl set-timezone Europe/Paris
  timedatectl status        # « System clock synchronized: yes »
  ```

## 5. Paquets

```bash
sudo apt update
sudo apt install git python3 python3-venv \
  pipewire pipewire-pulse wireplumber pulseaudio-utils pavucontrol \
  easyeffects butt ffmpeg usbutils procps ufw
```

Vérifications :

```bash
python3 --version                       # 3.13.x
pactl info | grep "Server Name"         # « PulseAudio (on PipeWire …) »
ffmpeg -hide_banner -devices | grep pulse
ffmpeg -hide_banner -encoders | grep libmp3lame
```

## 6. Carte son Aureon et PipeWire

### Détection

```bash
lsusb | grep -i 0ccd:0028        # doit afficher la TerraTec Aureon
```

### Profil

Dans **pavucontrol**, onglet *Configuration*, choisir pour l'Aureon un profil qui inclut l'**entrée stéréo analogique** (par exemple « Duplex stéréo analogique »).
WirePlumber retient ce choix au redémarrage.

### Fréquence à 48 kHz

Le dashboard et les enregistrements travaillent en 48 kHz. Pour éviter tout rééchantillonnage, créer `~/.config/pipewire/pipewire.conf.d/10-clock-rate.conf` :

```
context.properties = {
    default.clock.rate          = 48000
    default.clock.allowed-rates = [ 48000 ]
}
```

```bash
systemctl --user restart wireplumber pipewire pipewire-pulse
```

### Réglage du niveau

Envoyer du son depuis la table, puis régler le gain d'entrée dans pavucontrol (onglet *Périphériques d'entrée*) : les crêtes doivent rester sous 0 dB.

## 7. EasyEffects

1. Lancer EasyEffects depuis la session graphique.
2. **Préférences** → activer **« Lancer le service au démarrage »**.
3. Onglet **Entrée** → désactiver « Utiliser le périphérique par défaut » et choisir l'**Aureon** comme périphérique d'entrée.
4. Ajouter les traitements voulus (compresseur, limiteur…), puis **enregistrer un preset** et le charger par défaut.
5. Vérifier que la source virtuelle est bien exposée :
   ```bash
   pactl list short sources | grep easyeffects_source
   # … easyeffects_source … float32le 2ch 48000Hz …
   ```

> Le nom `easyeffects_source` est attendu tel quel par le dashboard : ne pas le renommer.

## 8. BUTT et AzuraCast

### Côté AzuraCast

Dans l'administration de la station, récupérer les paramètres de **connexion source / streamer** : serveur, port, point de montage, identifiant et mot de passe.

### Côté BUTT

Dans **Settings** :

- **Main → Server → ADD** : type *Icecast*, adresse `<azuracast.exemple.fr>`, port `<8005>`, mount `<point de montage>`, utilisateur et mot de passe AzuraCast ;
- **Audio** : périphérique *PulseAudio* (ou *default*), **48000 Hz**, **stéréo**, codec **MP3**, **192 kb/s** ;
- **Main** : cocher *Connect at startup* (le libellé peut varier selon la version) ;
- **Save settings**. La configuration est écrite dans `~/.buttrc`, qui ne doit jamais être versionné.

Lancer BUTT une première fois, puis dans **pavucontrol**, onglet *Enregistrement* : faire enregistrer BUTT depuis **« Easy Effects Source »**. PipeWire retient cette association.

### Démarrage automatique de BUTT

`~/.config/autostart/butt.desktop` :

```ini
[Desktop Entry]
Type=Application
Name=BUTT
Exec=butt
X-GNOME-Autostart-enabled=true
```

## 9. Énergie et démarrage automatique

L'encodeur ne doit jamais se mettre en veille :

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
# GNOME :
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
```

Dans le BIOS/UEFI, activer si possible le **redémarrage automatique après coupure de courant** (*Restore on AC power loss*).

## 10. Dashboard

```bash
mkdir -p ~/recordings/manual
```

Installer ensuite le dashboard et son service systemd utilisateur en suivant le [README](../README.md#installation) (sections *Installation* et *Lancement → Production*), sans oublier :

```bash
sudo loginctl enable-linger <encodeur>
```

Si les enregistrements vont sur un disque externe, le monter sous `/media` ou `/mnt`, ou l'ajouter à `VICHY_DASHBOARD_ALLOWED_ROOTS`.

## 11. Watchdog audio

Le dashboard **lit** l'état du watchdog dans `/tmp/vichy-audio-watchdog.json`, mais ne l'écrit pas.
Ce fichier est produit par un script de watchdog audio **séparé**, propre à l'encodeur.

> ⚠️ **À compléter** : la source de ce script n'est pas versionnée et doit être retrouvée.
> Son installation (emplacement, service systemd, démarrage automatique) sera documentée ici.
> Idéalement, le script sera ajouté à ce dépôt.

Format attendu par le dashboard :

```json
{
  "active": true,
  "recovery_count": 0,
  "last_incident": null,
  "last_recovery": null
}
```

Si ce fichier est absent, le dashboard affiche le watchdog comme inactif.

## 12. Pare-feu

```bash
sudo ufw default deny incoming
sudo ufw allow from <192.168.1.0/24> to any port 22 proto tcp
sudo ufw allow from <192.168.1.0/24> to any port 8080 proto tcp
sudo ufw enable
```

## 13. Recette finale

Après un **redémarrage complet** du PC, sans aucune action manuelle :

```bash
lsusb | grep -i 0ccd:0028                         # Aureon présente
pgrep -x easyeffects && pgrep -x butt             # deux PID affichés
pactl list short sources | grep easyeffects_source
systemctl --user status vichy-dashboard           # active (running)
curl -s http://localhost:8080/api/status | head -c 300
```

Puis, depuis un poste de la régie, sur `http://<ip-encodeur>:8080` :

- [ ] le VU-mètre bouge avec le son de la table ;
- [ ] Aureon, EasyEffects et BUTT sont au vert ;
- [ ] le flux est reçu par AzuraCast (lecteur public de la station) ;
- [ ] un enregistrement de test de 30 s en FLAC se lit correctement.

## 14. Dépannage

| Symptôme | Piste |
|---|---|
| Aureon « absente » | `lsusb` : changer de port USB, éviter les hubs |
| VU-mètre à plat, « source indisponible » | EasyEffects arrêté, ou entrée EasyEffects pas réglée sur l'Aureon |
| VU-mètre à plat alors qu'EasyEffects tourne | Profil de l'Aureon sans entrée (pavucontrol → *Configuration*) |
| BUTT connecté mais flux muet | BUTT n'enregistre pas depuis « Easy Effects Source » (pavucontrol → *Enregistrement*) |
| Rien ne démarre après un reboot | Connexion automatique désactivée, ou linger non activé |
| Dashboard inaccessible depuis la régie | `ufw status`, IP de l'encodeur, service `vichy-dashboard` |
| Enregistrement refusé (`403`) | Dossier hors de `VICHY_DASHBOARD_ALLOWED_ROOTS` |
