#!/usr/bin/env bash
# Prepares the Claude SEO Python runtime in Claude Code on the web sessions.
# Local installs use install.sh or /plugin install instead, so this is a no-op there.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

# One data dir shared by this hook and the plugin's own runtime calls
# (CLAUDE_SEO_DATA_DIR takes precedence over CLAUDE_PLUGIN_DATA).
data_dir="${HOME}/.local/share/claude-seo"
chromium="/opt/pw-browsers/chromium"

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo "export CLAUDE_SEO_DATA_DIR=\"${data_dir}\"" >> "${CLAUDE_ENV_FILE}"
    # Skills and agents load from .claude/ symlinks into this checkout, so the
    # checkout plays the plugin root for "${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo".
    echo "export CLAUDE_PLUGIN_ROOT=\"${CLAUDE_PROJECT_DIR:-$(pwd)}\"" >> "${CLAUDE_ENV_FILE}"
    # All egress goes through the sandbox's local CONNECT proxy (127.0.0.1).
    echo "export CLAUDE_SEO_ALLOW_LOOPBACK_PROXY=1" >> "${CLAUDE_ENV_FILE}"
    # The sandbox blocks Playwright's browser CDN; reuse the preinstalled Chromium.
    if [ -x "${chromium}" ]; then
        echo "export CLAUDE_SEO_CHROMIUM_PATH=\"${chromium}\"" >> "${CLAUDE_ENV_FILE}"
    fi
fi

# Google APIs (Search Console, GA4, Indexing): cloud environments hold secrets
# as variables, so materialize the service account key (raw or base64 JSON).
if [ -n "${GOOGLE_SERVICE_ACCOUNT_JSON:-}" ]; then
    sa_file="${HOME}/.config/claude-seo/service_account.json"
    mkdir -p "$(dirname "${sa_file}")"
    (
        umask 077
        if printf '%s' "${GOOGLE_SERVICE_ACCOUNT_JSON}" | grep -q '^[[:space:]]*{'; then
            printf '%s' "${GOOGLE_SERVICE_ACCOUNT_JSON}" > "${sa_file}"
        else
            printf '%s' "${GOOGLE_SERVICE_ACCOUNT_JSON}" | base64 -d > "${sa_file}"
        fi
    )
    if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
        echo "export GOOGLE_APPLICATION_CREDENTIALS=\"${sa_file}\"" >> "${CLAUDE_ENV_FILE}"
    fi
fi
# httplib2 and gRPC ignore REQUESTS_CA_BUNDLE; point them at the sandbox proxy CA.
if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${SSL_CERT_FILE:-}" ]; then
    echo "export HTTPLIB2_CA_CERTS=\"${SSL_CERT_FILE}\"" >> "${CLAUDE_ENV_FILE}"
    echo "export GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=\"${SSL_CERT_FILE}\"" >> "${CLAUDE_ENV_FILE}"
fi

launcher="${CLAUDE_PROJECT_DIR:-$(pwd)}/scripts/claude-seo"
if CLAUDE_SEO_DATA_DIR="${data_dir}" "${launcher}" doctor --json 2>/dev/null | grep -q '"ready": true'; then
    exit 0
fi

# Chromium comes from the preinstalled browser above, so skip the download.
CLAUDE_SEO_DATA_DIR="${data_dir}" "${launcher}" setup --skip-browser
