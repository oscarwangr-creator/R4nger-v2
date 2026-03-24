#!/usr/bin/env bash
# ============================================================
# RTF v2.0 — Full Tool Installer
# Installs all 80+ tools across 13 operational domains
#
# Usage:
#   ./tools/install_all_tools.sh                  # install everything
#   ./tools/install_all_tools.sh --category recon # only one category
#   ./tools/install_all_tools.sh --skip-apt       # skip apt packages
#   ./tools/install_all_tools.sh --skip-go        # skip Go tools
#   ./tools/install_all_tools.sh --skip-pip       # skip pip/pipx tools
#   ./tools/install_all_tools.sh --skip-repos     # skip git clone repos
#   ./tools/install_all_tools.sh --dry-run        # print what would run
#
# AUTHORIZED USE ONLY — ensure written permission before use
# ============================================================
set -euo pipefail

# ── Colours ─────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}[+]${RESET} $*"; }
warn() { echo -e "${YELLOW}[!]${RESET} $*"; }
err()  { echo -e "${RED}[-]${RESET} $*"; }
info() { echo -e "${CYAN}[*]${RESET} $*"; }
hdr()  { echo -e "\n${BOLD}${CYAN}══ $* ══${RESET}"; }

# ── Defaults ────────────────────────────────────────────────
TOOLS_DIR="${TOOLS_DIR:-$HOME/redteam-lab/tools}"
WORDLISTS="${WORDLISTS:-$HOME/redteam-lab/wordlists}"
LOG_FILE="${LOG_FILE:-$HOME/redteam-lab/logs/install_$(date +%Y%m%d_%H%M%S).log}"
DRY_RUN=0
SKIP_APT=0; SKIP_GO=0; SKIP_PIP=0; SKIP_REPOS=0; SKIP_RUST=0
CATEGORY=""

# ── Parse args ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)       DRY_RUN=1 ;;
    --skip-apt)      SKIP_APT=1 ;;
    --skip-go)       SKIP_GO=1 ;;
    --skip-pip)      SKIP_PIP=1 ;;
    --skip-repos)    SKIP_REPOS=1 ;;
    --skip-rust)     SKIP_RUST=1 ;;
    --category)      CATEGORY="$2"; shift ;;
    --tools-dir)     TOOLS_DIR="$2"; shift ;;
    -h|--help)
      echo "Usage: $0 [--dry-run] [--skip-apt|go|pip|repos|rust] [--category NAME]"
      exit 0 ;;
  esac
  shift
done

# ── Setup ───────────────────────────────────────────────────
mkdir -p "$TOOLS_DIR" "$WORDLISTS" "$(dirname "$LOG_FILE")"
exec > >(tee -a "$LOG_FILE") 2>&1

START_TS=$(date +%s)
INSTALLED=0; FAILED=0; SKIPPED=0

banner() {
  echo -e "${BOLD}"
  echo " ██████╗ ████████╗███████╗  TOOL INSTALLER"
  echo " ██╔══██╗╚══██╔══╝██╔════╝  RTF v2.0"
  echo " ██████╔╝   ██║   █████╗    ════════════"
  echo " ██╔══██╗   ██║   ██╔══╝"
  echo " ██║  ██║   ██║   ██║"
  echo " ╚═╝  ╚═╝   ╚═╝   ╚═╝"
  echo -e "${RESET}"
  info "Tools dir : $TOOLS_DIR"
  info "Log file  : $LOG_FILE"
  [[ $DRY_RUN -eq 1 ]] && warn "DRY RUN — no commands will execute"
  echo ""
}

# ── Helpers ─────────────────────────────────────────────────
is_installed() { command -v "$1" &>/dev/null; }

run_cmd() {
  local desc="$1"; shift
  if [[ $DRY_RUN -eq 1 ]]; then
    info "[DRY] $desc → $*"; return 0
  fi
  info "Installing: $desc"
  if "$@"; then
    ok "$desc ✓"; ((INSTALLED++)); return 0
  else
    err "$desc ✗ (non-fatal, continuing)"; ((FAILED++)); return 1
  fi
}

# Retry wrapper: 3 attempts with exponential backoff
retry_cmd() {
  local desc="$1"; shift
  local attempts=3; local wait=2
  for i in $(seq 1 $attempts); do
    if run_cmd "$desc" "$@"; then return 0; fi
    [[ $i -lt $attempts ]] && { warn "Retry $i/$attempts for $desc in ${wait}s…"; sleep $wait; wait=$((wait*2)); }
  done
  return 1
}

skip_if_installed() {
  local bin="$1"; local desc="$2"
  if is_installed "$bin"; then
    ok "$desc already installed → skipping"; ((SKIPPED++)); return 0
  fi
  return 1
}

apt_install() {
  [[ $SKIP_APT -eq 1 ]] && { warn "Skipping APT: $*"; return 0; }
  [[ $DRY_RUN -eq 1 ]] && { info "[DRY] apt install $*"; return 0; }
  sudo apt-get install -y -qq "$@" 2>/dev/null || warn "apt install $* failed (non-fatal)"
}

go_install() {
  [[ $SKIP_GO -eq 1 ]] && { warn "Skipping Go: $1"; return 0; }
  is_installed "go" || { warn "Go not installed — skipping $1"; return 0; }
  local name="${1##*/}"; name="${name%%@*}"
  skip_if_installed "$name" "$name" && return 0
  retry_cmd "$name (Go)" go install "$@"
}

pip_install() {
  [[ $SKIP_PIP -eq 1 ]] && { warn "Skipping pip: $1"; return 0; }
  retry_cmd "$1 (pip)" pip install --quiet --break-system-packages "$@" 2>/dev/null || \
  retry_cmd "$1 (pip3)" pip3 install --quiet "$@" 2>/dev/null || warn "pip install $1 failed"
}

pipx_install() {
  [[ $SKIP_PIP -eq 1 ]] && { warn "Skipping pipx: $1"; return 0; }
  is_installed "pipx" || pip_install pipx
  skip_if_installed "$1" "$1" && return 0
  retry_cmd "$1 (pipx)" pipx install "$1"
}

git_clone() {
  [[ $SKIP_REPOS -eq 1 ]] && { warn "Skipping clone: $2"; return 0; }
  local url="$1"; local dir="$TOOLS_DIR/$2"
  if [[ -d "$dir/.git" ]]; then
    ok "$2 already cloned → pulling"; [[ $DRY_RUN -eq 0 ]] && git -C "$dir" pull -q
    ((SKIPPED++)); return 0
  fi
  retry_cmd "$2 (git clone)" git clone --depth=1 -q "$url" "$dir"
}

rust_install() {
  [[ $SKIP_RUST -eq 1 ]] && { warn "Skipping cargo: $1"; return 0; }
  is_installed "cargo" || { warn "Rust/cargo not installed — skipping $1"; return 0; }
  skip_if_installed "$1" "$1" && return 0
  retry_cmd "$1 (cargo)" cargo install "$1" --quiet
}

# ── Category gate ───────────────────────────────────────────
should_run() {
  [[ -z "$CATEGORY" ]] && return 0
  [[ "$CATEGORY" == "$1" ]] && return 0
  return 1
}

# ════════════════════════════════════════════════════════════
# SECTION 0 — PREREQUISITES
# ════════════════════════════════════════════════════════════
should_run "prereqs" && {
hdr "Prerequisites"
if [[ $SKIP_APT -eq 0 ]]; then
  info "Updating APT package lists…"
  [[ $DRY_RUN -eq 0 ]] && sudo apt-get update -qq
  apt_install curl wget git python3 python3-pip python3-dev \
              build-essential libssl-dev libffi-dev nmap nikto \
              ruby ruby-dev golang-go default-jre \
              libpcap-dev libnetfilter-queue-dev \
              unzip p7zip-full
  # pipx
  pip_install pipx
  [[ $DRY_RUN -eq 0 ]] && pipx ensurepath 2>/dev/null || true
fi
# Go path
[[ -d /usr/local/go/bin ]] && export PATH="$PATH:/usr/local/go/bin"
[[ -d "$HOME/go/bin" ]]    && export PATH="$PATH:$HOME/go/bin"
}

# ════════════════════════════════════════════════════════════
# SECTION 1 — RECON TOOLS
# ════════════════════════════════════════════════════════════
should_run "recon" && {
hdr "1 — Recon Tools"

# Amass (Go)
skip_if_installed amass "amass" || \
  go_install "github.com/owasp-amass/amass/v4/...@latest"

# Subfinder (Go)
skip_if_installed subfinder "subfinder" || \
  go_install "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"

# Assetfinder (Go)
skip_if_installed assetfinder "assetfinder" || \
  go_install "github.com/tomnomnom/assetfinder@latest"

# Naabu (Go) — fast port scanner
skip_if_installed naabu "naabu" || \
  go_install "github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"

# httprobe (Go)
skip_if_installed httprobe "httprobe" || \
  go_install "github.com/tomnomnom/httprobe@latest"

# httpx (Go) — HTTP probe
skip_if_installed httpx "httpx" || \
  go_install "github.com/projectdiscovery/httpx/cmd/httpx@latest"

# dnsx (Go)
skip_if_installed dnsx "dnsx" || \
  go_install "github.com/projectdiscovery/dnsx/cmd/dnsx@latest"

# Gobuster (Go)
skip_if_installed gobuster "gobuster" || \
  go_install "github.com/OJ/gobuster/v3@latest"

# ffuf (Go) — fast web fuzzer
skip_if_installed ffuf "ffuf" || \
  go_install "github.com/ffuf/ffuf/v2@latest"

# feroxbuster (Rust)
skip_if_installed feroxbuster "feroxbuster" || \
  rust_install feroxbuster || \
  apt_install feroxbuster

# Dirsearch (Python)
skip_if_installed dirsearch "dirsearch" || {
  git_clone "https://github.com/maurosoria/dirsearch" "dirsearch"
  [[ $DRY_RUN -eq 0 ]] && pip_install dirsearch 2>/dev/null || true
}

# Whatweb (Ruby)
skip_if_installed whatweb "whatweb" || \
  run_cmd "whatweb" gem install whatweb 2>/dev/null || \
  apt_install whatweb

# Photon (Python)
skip_if_installed photon "photon" || \
  git_clone "https://github.com/s0md3v/Photon" "photon"

# VHostScan (Python)
skip_if_installed VHostScan "VHostScan" || {
  git_clone "https://github.com/codingo/VHostScan" "VHostScan"
  [[ -d "$TOOLS_DIR/VHostScan" && $DRY_RUN -eq 0 ]] && \
    pip_install -r "$TOOLS_DIR/VHostScan/requirements.txt" 2>/dev/null || true
}

# AltDNS (Python)
skip_if_installed altdns "altdns" || \
  pip_install altdns

# altdns / dnstwist
skip_if_installed dnstwist "dnstwist" || pip_install dnstwist

# recon-ng (Python)
skip_if_installed recon-ng "recon-ng" || {
  git_clone "https://github.com/lanmaster53/recon-ng" "recon-ng"
  [[ -d "$TOOLS_DIR/recon-ng" && $DRY_RUN -eq 0 ]] && \
    pip_install -r "$TOOLS_DIR/recon-ng/REQUIREMENTS" 2>/dev/null || true
}

# SpiderFoot (Python)
skip_if_installed spiderfoot "spiderfoot" || {
  git_clone "https://github.com/smicallef/spiderfoot" "spiderfoot"
  [[ -d "$TOOLS_DIR/spiderfoot" && $DRY_RUN -eq 0 ]] && \
    pip_install -r "$TOOLS_DIR/spiderfoot/requirements.txt" 2>/dev/null || true
}

# Aquatone (Go)
skip_if_installed aquatone "aquatone" || \
  go_install "github.com/michenriksen/aquatone@latest"

# Altdns (pip)
pip_install altdns 2>/dev/null || true
}

# ════════════════════════════════════════════════════════════
# SECTION 2 — OSINT TOOLS
# ════════════════════════════════════════════════════════════
should_run "osint" && {
hdr "2 — OSINT Tools"

# Sherlock (pipx)
skip_if_installed sherlock "sherlock" || pipx_install sherlock-project

# Maigret (pipx)
skip_if_installed maigret "maigret" || pipx_install maigret

# Holehe (pipx)
skip_if_installed holehe "holehe" || pipx_install holehe

# H8mail (pip)
skip_if_installed h8mail "h8mail" || pip_install h8mail

# Social-Analyzer (pip)
skip_if_installed social-analyzer "social-analyzer" || pip_install social-analyzer

# theHarvester (pip)
skip_if_installed theHarvester "theHarvester" || pip_install theHarvester

# OSINTgram (Python)
skip_if_installed osintgram "osintgram" || {
  git_clone "https://github.com/Datalux/Osintgram" "osintgram"
  [[ -d "$TOOLS_DIR/osintgram" && $DRY_RUN -eq 0 ]] && \
    pip_install -r "$TOOLS_DIR/osintgram/requirements.txt" 2>/dev/null || true
}

# PhoneInfoga (Go)
skip_if_installed phoneinfoga "phoneinfoga" || \
  go_install "github.com/sundowndev/phoneinfoga/v2/cmd/phoneinfoga@latest"

# Profil3r (Python)
skip_if_installed profil3r "profil3r" || \
  git_clone "https://github.com/Greyjedix/Profil3r" "profil3r"

# Scrapling (pip)
pip_install scrapling 2>/dev/null || true

# IntelX CLI (Python)
pip_install intelx 2>/dev/null || true

# emailrep (pip)
pip_install emailrep 2>/dev/null || true

# GHunt (Python)
skip_if_installed ghunt "ghunt" || pip_install ghunt 2>/dev/null || \
  git_clone "https://github.com/mxrch/GHunt" "ghunt"

# TruffleHog (pip/Go)
skip_if_installed trufflehog "trufflehog" || \
  go_install "github.com/trufflesecurity/trufflehog/v3@latest" 2>/dev/null || \
  pip_install trufflehog 2>/dev/null || true

# GitLeaks (Go)
skip_if_installed gitleaks "gitleaks" || \
  go_install "github.com/gitleaks/gitleaks/v8@latest"

# Metagoofil (Python)
skip_if_installed metagoofil "metagoofil" || \
  git_clone "https://github.com/opsdisk/metagoofil" "metagoofil"

# URLScan CLI
pip_install urlscan 2>/dev/null || true

# snoop (Russian social networks)
skip_if_installed snoop "snoop" || \
  git_clone "https://github.com/snooppr/snoop" "snoop"

# socialscan (pip)
skip_if_installed socialscan "socialscan" || pip_install socialscan

# twint (Python) — deprecated but still useful
pip_install twint 2>/dev/null || true

# instaloader
skip_if_installed instaloader "instaloader" || pip_install instaloader

# gitfive (Python)
pip_install gitfive 2>/dev/null || \
  git_clone "https://github.com/mxrch/GitFive" "gitfive"
}

# ════════════════════════════════════════════════════════════
# SECTION 3 — VULNERABILITY SCANNING
# ════════════════════════════════════════════════════════════
should_run "scanning" && {
hdr "3 — Vulnerability Scanning"

# Nuclei (Go)
skip_if_installed nuclei "nuclei" || \
  go_install "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"

# Update nuclei templates
[[ $DRY_RUN -eq 0 ]] && is_installed nuclei && nuclei -update-templates -silent 2>/dev/null || true

# Nikto (Perl)
skip_if_installed nikto "nikto" || apt_install nikto

# Lynis (bash)
skip_if_installed lynis "lynis" || apt_install lynis

# Trivy (Go/apt)
skip_if_installed trivy "trivy" || {
  if command -v apt-get &>/dev/null; then
    [[ $DRY_RUN -eq 0 ]] && {
      wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key 2>/dev/null | \
        sudo apt-key add - 2>/dev/null || true
      echo "deb https://aquasecurity.github.io/trivy-repo/deb stable main" | \
        sudo tee /etc/apt/sources.list.d/trivy.list >/dev/null 2>&1 || true
      sudo apt-get update -qq 2>/dev/null || true
    }
    apt_install trivy
  else
    go_install "github.com/aquasecurity/trivy/cmd/trivy@latest"
  fi
}

# Kubescape
skip_if_installed kubescape "kubescape" || {
  [[ $DRY_RUN -eq 0 ]] && \
    curl -s https://raw.githubusercontent.com/kubescape/kubescape/master/install.sh | bash 2>/dev/null || true
}

# Vuls (Go)
skip_if_installed vuls "vuls" || {
  go_install "github.com/future-architect/vuls@latest" 2>/dev/null || true
}

# Scan4all (Go)
skip_if_installed scan4all "scan4all" || \
  go_install "github.com/GangZhuo/scan4all@latest" 2>/dev/null || true

# OpenVAS (apt — heavy)
if [[ "${INSTALL_OPENVAS:-0}" == "1" ]]; then
  skip_if_installed openvas "openvas" || {
    apt_install openvas 2>/dev/null || \
    apt_install gvm 2>/dev/null || true
    [[ $DRY_RUN -eq 0 ]] && sudo gvm-setup 2>/dev/null || true
  }
else
  warn "Skipping OpenVAS (set INSTALL_OPENVAS=1 to enable — requires 2GB+ and long setup)"
fi
}

# ════════════════════════════════════════════════════════════
# SECTION 4 — WEB EXPLOITATION
# ════════════════════════════════════════════════════════════
should_run "web" && {
hdr "4 — Web Exploitation"

# SQLMap (Python)
skip_if_installed sqlmap "sqlmap" || {
  pip_install sqlmap 2>/dev/null || \
  git_clone "https://github.com/sqlmapproject/sqlmap" "sqlmap"
}

# XSStrike (Python)
skip_if_installed xsstrike "xsstrike" || \
  git_clone "https://github.com/s0md3v/XSStrike" "xsstrike"

# Dalfox (Go)
skip_if_installed dalfox "dalfox" || \
  go_install "github.com/hahwul/dalfox/v2@latest"

# Commix (Python)
skip_if_installed commix "commix" || {
  git_clone "https://github.com/commixproject/commix" "commix"
  apt_install commix 2>/dev/null || true
}

# NoSQLMap (Python)
skip_if_installed nosqlmap "nosqlmap" || \
  git_clone "https://github.com/codingo/NoSQLMap" "nosqlmap"

# SSRFmap (Python)
skip_if_installed ssrfmap "ssrfmap" || \
  git_clone "https://github.com/swisskyrepo/SSRFmap" "ssrfmap"

# Wfuzz (pip)
skip_if_installed wfuzz "wfuzz" || pip_install wfuzz

# WPScan (Ruby)
skip_if_installed wpscan "wpscan" || \
  run_cmd "wpscan" gem install wpscan 2>/dev/null || \
  apt_install wpscan 2>/dev/null || true

# JoomScan (Perl)
skip_if_installed joomscan "joomscan" || \
  git_clone "https://github.com/OWASP/joomscan" "joomscan"

# Droopescan (pip)
skip_if_installed droopescan "droopescan" || pip_install droopescan

# CMSeeK (Python)
skip_if_installed cmseek "cmseek" || \
  git_clone "https://github.com/Tuhinshubhra/CMSeeK" "cmseek"

# OWASP ZAP (apt/snap)
if [[ "${INSTALL_ZAP:-0}" == "1" ]]; then
  apt_install zaproxy 2>/dev/null || snap install zaproxy --classic 2>/dev/null || true
fi

# Arjun (Python) — hidden param discovery
skip_if_installed arjun "arjun" || pip_install arjun 2>/dev/null || true

# Param Miner / ParamSpider (Python)
skip_if_installed paramspider "paramspider" || pip_install paramspider 2>/dev/null || true
}

# ════════════════════════════════════════════════════════════
# SECTION 5 — CREDENTIAL ATTACKS
# ════════════════════════════════════════════════════════════
should_run "creds" && {
hdr "5 — Credential Attacks"

# Hydra (apt)
skip_if_installed hydra "hydra" || apt_install hydra

# Ncrack (apt)
skip_if_installed ncrack "ncrack" || apt_install ncrack

# Medusa (apt)
skip_if_installed medusa "medusa" || apt_install medusa

# Hashcat (apt/build)
skip_if_installed hashcat "hashcat" || apt_install hashcat

# John the Ripper (apt)
skip_if_installed john "john" || apt_install john

# Kerbrute (Go)
skip_if_installed kerbrute "kerbrute" || \
  go_install "github.com/ropnop/kerbrute@latest"

# BruteSpray (Python)
skip_if_installed brutespray "brutespray" || \
  pip_install brutespray 2>/dev/null || \
  git_clone "https://github.com/x90skysn3k/brutespray" "brutespray"

# CrackMapExec (pip)
skip_if_installed crackmapexec "crackmapexec" || skip_if_installed cme "cme" || {
  pip_install crackmapexec 2>/dev/null || \
  pip_install git+https://github.com/byt3bl33d3r/CrackMapExec.git 2>/dev/null || \
  pipx_install crackmapexec 2>/dev/null || true
}

# Spray (Python)
skip_if_installed spray "spray" || \
  go_install "github.com/Greenwolf/Spray@latest" 2>/dev/null || true

# Sprayhound (Python)
pip_install sprayhound 2>/dev/null || true

# Default credentials lists
if [[ $DRY_RUN -eq 0 ]]; then
  mkdir -p "$WORDLISTS"
  [[ ! -f "$WORDLISTS/rockyou.txt" ]] && {
    info "Downloading rockyou.txt…"
    wget -q "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt" \
         -O "$WORDLISTS/rockyou.txt" 2>/dev/null || true
  }
  [[ ! -d "$WORDLISTS/SecLists" ]] && {
    info "Cloning SecLists (may take a few minutes)…"
    git clone --depth=1 -q "https://github.com/danielmiessler/SecLists" \
      "$WORDLISTS/SecLists" 2>/dev/null || true
  }
fi
}

# ════════════════════════════════════════════════════════════
# SECTION 6 — EXPLOITATION FRAMEWORKS
# ════════════════════════════════════════════════════════════
should_run "exploitation" && {
hdr "6 — Exploitation Frameworks"

# Metasploit (apt/curl installer)
skip_if_installed msfconsole "metasploit" || {
  apt_install metasploit-framework 2>/dev/null || {
    warn "Trying Metasploit curl installer…"
    [[ $DRY_RUN -eq 0 ]] && \
      curl -s https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb 2>/dev/null | bash 2>/dev/null || true
  }
}

# OWTF (Python)
skip_if_installed owtf "owtf" || {
  git_clone "https://github.com/owtf/owtf" "owtf"
  [[ -d "$TOOLS_DIR/owtf" && $DRY_RUN -eq 0 ]] && \
    pip_install -r "$TOOLS_DIR/owtf/requirements.txt" 2>/dev/null || true
}

# AutoSploit (Python)
skip_if_installed autosploit "autosploit" || \
  git_clone "https://github.com/NullArray/AutoSploit" "autosploit"

# KubeSploit (Go)
skip_if_installed kubesploit "kubesploit" || \
  git_clone "https://github.com/cyberark/kubesploit" "kubesploit"

# Impacket (pip)
skip_if_installed impacket "impacket" || pip_install impacket
}

# ════════════════════════════════════════════════════════════
# SECTION 7 — POST-EXPLOITATION
# ════════════════════════════════════════════════════════════
should_run "post" && {
hdr "7 — Post-Exploitation"

# Evil-WinRM (Ruby gem)
skip_if_installed evil-winrm "evil-winrm" || {
  run_cmd "evil-winrm" gem install evil-winrm 2>/dev/null || \
  apt_install evil-winrm 2>/dev/null || true
}

# BloodHound (apt)
skip_if_installed bloodhound "bloodhound" || apt_install bloodhound 2>/dev/null || true
skip_if_installed neo4j "neo4j" || {
  apt_install neo4j 2>/dev/null || {
    warn "Trying Neo4j apt repo…"
    [[ $DRY_RUN -eq 0 ]] && {
      wget -qO - https://debian.neo4j.com/neotechnology.gpg.key 2>/dev/null | \
        sudo apt-key add - 2>/dev/null || true
      echo 'deb https://debian.neo4j.com stable latest' | \
        sudo tee /etc/apt/sources.list.d/neo4j.list >/dev/null 2>&1 || true
      sudo apt-get update -qq 2>/dev/null || true
    }
    apt_install neo4j 2>/dev/null || true
  }
}

# BloodHound.py (pip)
skip_if_installed bloodhound-python "bloodhound-python" || pip_install bloodhound 2>/dev/null || true

# SharpHound (clone for reference)
git_clone "https://github.com/BloodHoundAD/SharpHound" "sharphound" 2>/dev/null || true

# LinPEAS / WinPEAS
[[ $DRY_RUN -eq 0 && ! -d "$TOOLS_DIR/PEASS-ng" ]] && \
  git clone --depth=1 -q "https://github.com/carlospolop/PEASS-ng" \
    "$TOOLS_DIR/PEASS-ng" 2>/dev/null || true

# linenum (bash script)
[[ $DRY_RUN -eq 0 && ! -f "$TOOLS_DIR/LinEnum.sh" ]] && \
  wget -q "https://raw.githubusercontent.com/rebootuser/LinEnum/master/LinEnum.sh" \
       -O "$TOOLS_DIR/LinEnum.sh" 2>/dev/null || true

# Mimikatz (wine for Linux or reference binary)
git_clone "https://github.com/gentilkiwi/mimikatz" "mimikatz" 2>/dev/null || true

# WinPwn (PowerShell)
git_clone "https://github.com/S3cur3Th1sSh1t/WinPwn" "winpwn" 2>/dev/null || true

# PowerSploit
git_clone "https://github.com/PowerShellMafia/PowerSploit" "powersploit" 2>/dev/null || true

# Pwncat (pip)
skip_if_installed pwncat "pwncat" || pip_install pwncat 2>/dev/null || true

# Empire (Python)
if [[ "${INSTALL_EMPIRE:-0}" == "1" ]]; then
  git_clone "https://github.com/BC-SECURITY/Empire" "empire" 2>/dev/null || true
fi
}

# ════════════════════════════════════════════════════════════
# SECTION 8 — ACTIVE DIRECTORY
# ════════════════════════════════════════════════════════════
should_run "ad" && {
hdr "8 — Active Directory"
pip_install impacket 2>/dev/null || true
go_install "github.com/ropnop/kerbrute@latest" 2>/dev/null || true
skip_if_installed ldapsearch "ldapsearch" || apt_install ldap-utils
skip_if_installed enum4linux "enum4linux" || apt_install enum4linux 2>/dev/null || \
  git_clone "https://github.com/CiscoCXSecurity/enum4linux" "enum4linux"
}

# ════════════════════════════════════════════════════════════
# SECTION 9 — NETWORK & WIRELESS
# ════════════════════════════════════════════════════════════
should_run "network" && {
hdr "9 — Network & Wireless"

# Masscan (apt/build)
skip_if_installed masscan "masscan" || apt_install masscan || {
  git_clone "https://github.com/robertdavidgraham/masscan" "masscan"
  [[ -d "$TOOLS_DIR/masscan" && $DRY_RUN -eq 0 ]] && \
    (cd "$TOOLS_DIR/masscan" && make 2>/dev/null && sudo make install 2>/dev/null) || true
}

# Bettercap (Go)
skip_if_installed bettercap "bettercap" || {
  go_install "github.com/bettercap/bettercap@latest" 2>/dev/null || \
  apt_install bettercap 2>/dev/null || true
}

# mitmproxy (pip)
skip_if_installed mitmproxy "mitmproxy" || pip_install mitmproxy

# Responder (Python)
skip_if_installed responder "responder" || {
  git_clone "https://github.com/lgandx/Responder" "responder"
  apt_install python3-netifaces 2>/dev/null || true
}

# Sniffnet (Rust)
skip_if_installed sniffnet "sniffnet" || rust_install sniffnet 2>/dev/null || true

# Wireless
apt_install aircrack-ng 2>/dev/null || true
apt_install wireshark-common 2>/dev/null || true
apt_install tcpdump 2>/dev/null || true

# wifiphisher
skip_if_installed wifiphisher "wifiphisher" || {
  git_clone "https://github.com/wifiphisher/wifiphisher" "wifiphisher"
  apt_install wifiphisher 2>/dev/null || true
}

# hcxdumptool & hcxtools
skip_if_installed hcxdumptool "hcxdumptool" || apt_install hcxdumptool 2>/dev/null || {
  git_clone "https://github.com/ZerBea/hcxdumptool" "hcxdumptool"
  [[ -d "$TOOLS_DIR/hcxdumptool" && $DRY_RUN -eq 0 ]] && \
    (cd "$TOOLS_DIR/hcxdumptool" && make 2>/dev/null && sudo make install 2>/dev/null) || true
}
skip_if_installed hcxtools "hcxtools" || apt_install hcxtools 2>/dev/null || \
  git_clone "https://github.com/ZerBea/hcxtools" "hcxtools"
}

# ════════════════════════════════════════════════════════════
# SECTION 10 — REVERSE ENGINEERING
# ════════════════════════════════════════════════════════════
should_run "re" && {
hdr "10 — Reverse Engineering"

# Radare2 (apt/build)
skip_if_installed r2 "radare2" || {
  apt_install radare2 2>/dev/null || {
    git_clone "https://github.com/radareorg/radare2" "radare2"
    [[ -d "$TOOLS_DIR/radare2" && $DRY_RUN -eq 0 ]] && \
      (cd "$TOOLS_DIR/radare2" && sys/install.sh 2>/dev/null) || true
  }
}

# Rizin (radare2 fork)
skip_if_installed rizin "rizin" || apt_install rizin 2>/dev/null || {
  [[ $DRY_RUN -eq 0 ]] && \
    curl -sfL https://github.com/rizinorg/rizin/releases/latest/download/rizin_amd64.deb \
         -o /tmp/rizin.deb 2>/dev/null && sudo dpkg -i /tmp/rizin.deb 2>/dev/null || true
}

# Ghidra (Java)
skip_if_installed ghidra "ghidra" || {
  [[ $DRY_RUN -eq 0 ]] && {
    GHIDRA_VER="11.1.2"
    GHIDRA_URL="https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GHIDRA_VER}_build/ghidra_${GHIDRA_VER}_PUBLIC_20240709.zip"
    wget -q "$GHIDRA_URL" -O /tmp/ghidra.zip 2>/dev/null && \
    unzip -q /tmp/ghidra.zip -d "$TOOLS_DIR/" 2>/dev/null && \
    sudo ln -sf "$TOOLS_DIR/ghidra_${GHIDRA_VER}_PUBLIC/ghidraRun" /usr/local/bin/ghidra 2>/dev/null || true
  }
}

# Bytecode-viewer (Java jar)
[[ $DRY_RUN -eq 0 && ! -f "$TOOLS_DIR/bytecode-viewer.jar" ]] && \
  wget -q "https://github.com/Konloch/bytecode-viewer/releases/latest/download/Bytecode-Viewer.jar" \
       -O "$TOOLS_DIR/bytecode-viewer.jar" 2>/dev/null || true

# pwndbg (GDB extension)
git_clone "https://github.com/pwndbg/pwndbg" "pwndbg" 2>/dev/null || true
pip_install pwntools 2>/dev/null || true

# strace/ltrace (apt)
apt_install strace ltrace binutils 2>/dev/null || true
}

# ════════════════════════════════════════════════════════════
# SECTION 11 — THREAT INTELLIGENCE
# ════════════════════════════════════════════════════════════
should_run "ti" && {
hdr "11 — Threat Intelligence"

# IntelOwl (Docker-based)
git_clone "https://github.com/intelowlproject/IntelOwl" "intelowl"
pip_install pyintelowl 2>/dev/null || true

# ThreatIngestor (pip)
pip_install threatingestor 2>/dev/null || true

# AIL-framework
git_clone "https://github.com/CIRCL/AIL-framework" "ail-framework" 2>/dev/null || true

# MISP PyMISP (pip)
pip_install pymisp 2>/dev/null || true

# OTX CLI (pip)
pip_install OTXv2 2>/dev/null || true

# Harpoon (pip)
pip_install harpoon 2>/dev/null || true

# Maltrail (Python)
git_clone "https://github.com/stamparm/maltrail" "maltrail" 2>/dev/null || true
}

# ════════════════════════════════════════════════════════════
# SECTION 12 — CLOUD SECURITY
# ════════════════════════════════════════════════════════════
should_run "cloud" && {
hdr "12 — Cloud Security"

# AWS CLI v2
skip_if_installed aws "aws-cli" || {
  [[ $DRY_RUN -eq 0 ]] && {
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
         -o /tmp/awscliv2.zip -s 2>/dev/null && \
    unzip -q /tmp/awscliv2.zip -d /tmp/ 2>/dev/null && \
    sudo /tmp/aws/install 2>/dev/null || true
  }
}

# Azure CLI
skip_if_installed az "azure-cli" || {
  [[ $DRY_RUN -eq 0 ]] && \
    curl -sL https://aka.ms/InstallAzureCLIDeb 2>/dev/null | sudo bash 2>/dev/null || true
}

# Prowler (pip)
skip_if_installed prowler "prowler" || pip_install prowler 2>/dev/null || true

# ScoutSuite (pip)
skip_if_installed scout "scoutsuite" || pip_install scoutsuite 2>/dev/null || true

# CloudMapper (Python)
git_clone "https://github.com/duo-labs/cloudmapper" "cloudmapper" 2>/dev/null || true

# Pacu (AWS exploitation)
git_clone "https://github.com/RhinoSecurityLabs/pacu" "pacu" 2>/dev/null || true
}

# ════════════════════════════════════════════════════════════
# SECTION 13 — AI TOOLS
# ════════════════════════════════════════════════════════════
should_run "ai" && {
hdr "13 — AI Tools"

# Anthropic SDK (pip)
pip_install anthropic 2>/dev/null || true

# OpenAI SDK (pip)
pip_install openai 2>/dev/null || true

# LangChain (pip)
pip_install langchain 2>/dev/null || true

# PentestGPT (pip)
pip_install pentestgpt 2>/dev/null || \
  git_clone "https://github.com/GreyDGL/PentestGPT" "pentestgpt" 2>/dev/null || true

# GPT Researcher
git_clone "https://github.com/assafelovic/gpt-researcher" "gpt-researcher" 2>/dev/null || true
}

# ════════════════════════════════════════════════════════════
# SECTION 14 — RTF PYTHON DEPENDENCIES
# ════════════════════════════════════════════════════════════
should_run "rtf_deps" && {
hdr "14 — RTF Core Dependencies"
RTF_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "$RTF_ROOT/requirements.txt" ]] && \
  pip_install -r "$RTF_ROOT/requirements.txt" 2>/dev/null || true

pip_install httpx aiohttp fastapi uvicorn flask rich click \
            jinja2 pyyaml openpyxl reportlab python-docx \
            networkx matplotlib requests beautifulsoup4 \
            lxml chardet colorama tabulate 2>/dev/null || true
}

# ════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════════════
END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))
echo ""
echo -e "${BOLD}════════════════════════════════════════${RESET}"
echo -e "${BOLD}INSTALLATION COMPLETE${RESET}"
echo -e "${BOLD}════════════════════════════════════════${RESET}"
echo -e "  ${GREEN}Installed:${RESET}  $INSTALLED"
echo -e "  ${YELLOW}Skipped:${RESET}    $SKIPPED (already present)"
echo -e "  ${RED}Failed:${RESET}     $FAILED (non-fatal)"
echo -e "  Time:       ${ELAPSED}s"
echo -e "  Log:        $LOG_FILE"
echo ""
echo -e "Run ${CYAN}python rtf.py tools list --installed${RESET} to verify."
echo -e "Run ${CYAN}./tools/verify_versions.sh${RESET} to check tool versions."
echo ""
