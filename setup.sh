mkdir -p ~/.streamlit

cat > ~/.streamlit/config.toml << EOF
[server]
headless = true
enableCORS = false
port = $PORT

[theme]
base = "light"
primaryColor = "#2F5496"
backgroundColor = "#f4f6f9"
secondaryBackgroundColor = "#ffffff"
textColor = "#1a1a2e"
EOF
