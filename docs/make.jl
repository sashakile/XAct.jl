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

# Export Pluto notebooks as Documenter-compatible Markdown
pluto_dir = joinpath(@__DIR__, "..", "notebooks", "pluto")
pluto_output = joinpath(@__DIR__, "src", "notebooks")
isdir(pluto_output) || mkdir(pluto_output)

if isdir(pluto_dir) && !isempty(filter(f -> endswith(f, ".jl"), readdir(pluto_dir)))
    using PlutoStaticHTML
    pluto_files = filter(f -> endswith(f, ".jl"), readdir(pluto_dir))
    bopts = BuildOptions(pluto_dir; write_files=false, output_format=documenter_output)
    results = build_notebooks(bopts, pluto_files)
    for file in pluto_files
        name = replace(file, ".jl" => "")
        outpath = joinpath(pluto_output, "$name.md")
        content = join(results[file], "\n")
        @info "Writing Pluto output: $outpath ($(length(content)) bytes)"
        write(outpath, content)
    end
end

makedocs(;
    sitename="xAct.jl",
    format=Documenter.HTML(;
        prettyurls=get(ENV, "CI", nothing) == "true",
        canonical="https://sashakile.github.io/sxAct/",
        edit_link="main",
        assets=String[],
        size_threshold=300 * 1024, # Increase to 300KiB for large API page
        inventory_version="0.4.0",
    ),
    modules=[xAct, xAct.XCore, xAct.XPerm, xAct.XTensor, xAct.XInvar],
    pages=[
        "Home" => "index.md",
        "Status" => "theory/STATUS.md",
        "Installation" => "installation.md",
        "Getting Started" => "getting-started.md",
        "Migrating from Wolfram" => "wolfram-migration.md",
        "Tutorials" =>
            ["Basics" => "examples/basics.md", "Riemann Invariants" => "examples/invar.md"],
        "Notebooks" => ["Interactive Basics (Pluto)" => "notebooks/basics.md"],
        "Theory" => ["Differential Geometry Primer" => "differential-geometry-primer.md"],
        "Advanced" => ["Oracle Quirks" => "theory/oracle-quirks.md"],
        "Architecture" => "architecture.md",
        "Reference" => [
            "Julia API" => "api.md",
            "Python API" => "api-python.md",
            "Verification API" => "api-verification.md",
            "Verification Tools" => "verification-tools.md",
        ],
        "Contributing" => "contributing.md",
    ],
)

deploydocs(; repo="github.com/sashakile/sxAct.git", devbranch="main")
