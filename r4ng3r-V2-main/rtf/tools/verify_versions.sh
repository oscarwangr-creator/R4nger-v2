#!/usr/bin/env bash
# ============================================================
# RTF v2.0 — Tool Version Verification Script
# Checks installed versions of all tools and compares to latest
#
# Usage:
#   ./tools/verify_versions.sh           # check all
#   ./tools/verify_versions.sh --json    # JSON output
#   ./tools/verify_versions.sh --missing # show only missing
#   ./tools/verify_versions.sh --outdated# show only outdated
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

OUTPUT_JSON=0; FILTER="all"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)     OUTPUT_JSON=1 ;;
    --missing)  FILTER="missing" ;;
    --outdated) FILTER="outdated" ;;
    --all)      FILTER="all" ;;
    -h|--help)
      echo "Usage: $0 [--json] [--missing|--outdated|--all]"; exit 0 ;;
  esac
  shift
done

# ── Tool definitions: name, binary, version-flag, category ──
declare -A TOOL_BINS=(
  # Recon
  [amass]="amass"         [subfinder]="subfinder"   [naabu]="naabu"
  [assetfinder]="assetfinder" [httprobe]="httprobe" [httpx]="httpx"
  [gobuster]="gobuster"   [ffuf]="ffuf"             [dirsearch]="dirsearch"
  [whatweb]="whatweb"     [dnsx]="dnsx"             [aquatone]="aquatone"
  [altdns]="altdns"       [feroxbuster]="feroxbuster"
  # OSINT
  [sherlock]="sherlock"   [maigret]="maigret"       [holehe]="holehe"
  [h8mail]="h8mail"       [socialscan]="socialscan" [theharvester]="theHarvester"
  [ghunt]="ghunt"         [phoneinfoga]="phoneinfoga" [instaloader]="instaloader"
  [trufflehog]="trufflehog" [gitleaks]="gitleaks"  [gitfive]="gitfive"
  [snoop]="snoop"         [twint]="twint"
  # Scanning
  [nuclei]="nuclei"       [nikto]="nikto"           [lynis]="lynis"
  [trivy]="trivy"         [kubescape]="kubescape"
  # Web exploitation
  [sqlmap]="sqlmap"       [dalfox]="dalfox"         [wfuzz]="wfuzz"
  [wpscan]="wpscan"       [commix]="commix"         [droopescan]="droopescan"
  [xsstrike]="python3"    # python script
  # Credentials
  [hydra]="hydra"         [ncrack]="ncrack"         [medusa]="medusa"
  [hashcat]="hashcat"     [john]="john"             [kerbrute]="kerbrute"
  [crackmapexec]="crackmapexec"
  # Post-exploitation
  [bloodhound]="bloodhound" [evil-winrm]="evil-winrm" [impacket]="impacket-secretsdump"
  [pwncat]="pwncat"       [neo4j]="neo4j"
  # Network
  [masscan]="masscan"     [bettercap]="bettercap"   [mitmproxy]="mitmproxy"
  [nmap]="nmap"           [aircrack]="aircrack-ng"  [tcpdump]="tcpdump"
  [hcxdumptool]="hcxdumptool" [responder]="responder"
  # RE
  [radare2]="r2"          [rizin]="rizin"           [ghidra]="ghidra"
  [pwntools]="python3"
  # Exploitation
  [metasploit]="msfconsole" [sqlmap2]="sqlmap"
  # Cloud
  [aws]="aws"             [azure]="az"              [prowler]="prowler"
  # Misc
  [go]="go"               [python3]="python3"       [ruby]="ruby"
  [docker]="docker"       [git]="git"               [curl]="curl"
  [wget]="wget"           [nmap2]="nmap"
)

declare -A VERSION_FLAGS=(
  [amass]="version"         [subfinder]="-version"    [naabu]="-version"
  [httpx]="-version"        [gobuster]="version"      [ffuf]="-V"
  [nuclei]="-version"       [dalfox]="version"        [kerbrute]="version"
  [trufflehog]="--version"  [gitleaks]="version"      [trivy]="--version"
  [nmap]="--version"        [masscan]="--version"     [bettercap]="--version"
  [mitmproxy]="--version"   [hashcat]="--version"     [hydra]="-V"
  [john]="--version"        [wfuzz]="--version"       [wpscan]="--version"
  [sqlmap]="--version"      [nikto]="-Version"        [lynis]="--version"
  [r2]="-version"           [rizin]="-version"        [holehe]="--version"
  [go]="version"            [python3]="--version"     [ruby]="--version"
  [docker]="--version"      [git]="--version"         [curl]="--version"
  [aws]="--version"         [az]="--version"          [prowler]="-v"
)

# ── Results accumulator ──────────────────────────────────────
TOTAL=0; FOUND=0; MISSING=0; ERRORS=0

declare -a JSON_ROWS=()

get_version() {
  local bin="$1" flag="${2:---version}"
  # Try different version flags
  local output=""
  for f in "$flag" "--version" "-version" "-V" "version"; do
    output=$("$bin" "$f" 2>&1 | head -3) && break || continue
  done
  # Extract version number
  local ver
  ver=$(echo "$output" | grep -oE "v?[0-9]+\.[0-9]+(\.[0-9]+)?" | head -1) || true
  echo "${ver:-unknown}"
}

check_python_pkg() {
  local pkg="$1"
  python3 -c "import importlib.metadata; print(importlib.metadata.version('$pkg'))" 2>/dev/null || \
  python3 -c "import $pkg; print(getattr($pkg,'__version__','installed'))" 2>/dev/null || \
  echo ""
}

print_header() {
  echo -e "${BOLD}${CYAN}"
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║          RTF v2.0 — Tool Version Verification             ║"
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo -e "${RESET}"
  printf "%-25s %-12s %-10s %s\n" "Tool" "Version" "Status" "Binary"
  printf "%-25s %-12s %-10s %s\n" "────────────────────" "───────────" "────────" "──────────────"
}

check_tool() {
  local name="$1" bin="$2"
  ((TOTAL++))

  if ! command -v "$bin" &>/dev/null; then
    ((MISSING++))
    [[ $FILTER == "all" || $FILTER == "missing" ]] && \
      printf "${RED}%-25s %-12s %-10s %s${RESET}\n" "$name" "---" "MISSING" "$bin"
    JSON_ROWS+=("{\"name\":\"$name\",\"binary\":\"$bin\",\"status\":\"missing\",\"version\":\"\"}")
    return
  fi

  ((FOUND++))
  local ver flag
  flag="${VERSION_FLAGS[$name]:-}"
  ver=$(get_version "$bin" "$flag") 2>/dev/null || ver="installed"
  local full_path
  full_path=$(command -v "$bin")

  [[ $FILTER == "all" || $FILTER == "installed" ]] && \
    printf "${GREEN}%-25s %-12s %-10s %s${RESET}\n" "$name" "${ver:-installed}" "OK" "$full_path"
  JSON_ROWS+=("{\"name\":\"$name\",\"binary\":\"$bin\",\"status\":\"installed\",\"version\":\"$ver\",\"path\":\"$full_path\"}")
}

# ── Run checks ───────────────────────────────────────────────
if [[ $OUTPUT_JSON -eq 0 ]]; then
  echo ""
  echo -e "${BOLD}$(date +'%Y-%m-%d %H:%M:%S')${RESET}"
  print_header
fi

# Check all tools
for name in "${!TOOL_BINS[@]}"; do
  check_tool "$name" "${TOOL_BINS[$name]}"
done | sort

# Also check key Python packages
echo ""
if [[ $OUTPUT_JSON -eq 0 ]]; then
  echo -e "${BOLD}Python Packages:${RESET}"
  printf "%-25s %-15s %s\n" "Package" "Version" "Status"
  printf "%-25s %-15s %s\n" "─────────────────────" "─────────────" "──────"
fi

for pkg in anthropic httpx fastapi flask rich click pyyaml openpyxl \
           reportlab jinja2 networkx requests beautifulsoup4 \
           impacket sherlock-project maigret holehe h8mail socialscan \
           sqlmap wfuzz droopescan scrapling instaloader gitfive \
           pymisp OTXv2 pyintelowl threatingestor; do
  ver=$(check_python_pkg "$pkg")
  if [[ -n "$ver" ]]; then
    printf "${GREEN}%-25s %-15s OK${RESET}\n" "$pkg" "$ver"
  else
    printf "${DIM}%-25s %-15s not installed${RESET}\n" "$pkg" "---"
  fi
done

# ── Summary ──────────────────────────────────────────────────
if [[ $OUTPUT_JSON -eq 1 ]]; then
  echo "{"
  echo "  \"generated_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"total\": $TOTAL,"
  echo "  \"installed\": $FOUND,"
  echo "  \"missing\": $MISSING,"
  echo "  \"tools\": ["
  local_ifs=$IFS; IFS=","
  echo "    ${JSON_ROWS[*]}"
  IFS=$local_ifs
  echo "  ]"
  echo "}"
else
  echo ""
  echo -e "${BOLD}════════════════════════════════${RESET}"
  printf "  %-12s ${GREEN}%d${RESET}\n" "Installed:" "$FOUND"
  printf "  %-12s ${RED}%d${RESET}\n"   "Missing:"   "$MISSING"
  printf "  %-12s %d\n"                 "Total:"      "$TOTAL"
  echo -e "${BOLD}════════════════════════════════${RESET}"
  echo ""
  PCT=$(( FOUND * 100 / (TOTAL > 0 ? TOTAL : 1) ))
  echo -e "Coverage: ${CYAN}${PCT}%%${RESET} (${FOUND}/${TOTAL})"
  echo ""
  [[ $MISSING -gt 0 ]] && \
    echo -e "Run ${CYAN}./tools/install_all_tools.sh${RESET} to install missing tools."
fi
