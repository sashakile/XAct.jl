# xAct.jl - Command Runner

# Build the documentation using Documenter.jl
docs:
    julia --project=docs/ docs/make.jl

# Serve the documentation locally on http://localhost:8000
serve-docs: docs
    python3 -m http.server --directory docs/build 8000
