# Documenter.jl build script
# Run with: julia --project=docs/ docs/make.jl

using Documenter
using Literate
using xAct

# Transform Literate examples into Markdown
example_dir = joinpath(@__DIR__, "examples")
output_dir = joinpath(@__DIR__, "src/examples")
isdir(output_dir) || mkdir(output_dir)

for file in readdir(example_dir)
    if endswith(file, ".jl")
        Literate.markdown(joinpath(example_dir, file), output_dir; documenter=true)
    end
end

makedocs(;
    sitename="xAct.jl",
    format=Documenter.HTML(;
        prettyurls=get(ENV, "CI", nothing) == "true",
        canonical="https://sashakile.github.io/sxAct/",
        edit_link="main",
        assets=String[],
    ),
    modules=[xAct, xAct.XCore, xAct.XPerm, xAct.XTensor],
    pages=[
        "Home" => "index.md",
        "Examples" => ["Getting Started" => "examples/basics.md"],
        "Getting Started (legacy)" => "getting-started.md",
        "Installation" => "installation.md",
        "Architecture" => "architecture.md",
        "Differential Geometry Primer" => "differential-geometry-primer.md",
        "Theory" => [
            "Status" => "theory/STATUS.md",
            "Oracle Quirks" => "theory/oracle-quirks.md",
            "Tensor DSL Integration" => "theory/tensordsl-integration.md",
        ],
        "API Reference" =>
            ["Julia API" => "api.md", "Verification API" => "api-verification.md"],
        "Contributing" => "contributing.md",
    ],
)

deploydocs(; repo="github.com/sashakile/sxAct.git", devbranch="main")
