# Documenter.jl build script
# Run with: julia docs/julia/make.jl

using Documenter

# Uncomment when the Julia package exists:
# using SxAct

makedocs(
    sitename = "SxAct.jl",
    format = Documenter.HTML(
        prettyurls = get(ENV, "CI", nothing) == "true",
    ),
    modules = Module[],  # Replace with [SxAct] when ready
    pages = [
        "Home" => "index.md",
        "API Reference" => "api.md",
    ],
)

deploydocs(
    repo = "github.com/sashakile/sxAct.git",
    devbranch = "main",
)
