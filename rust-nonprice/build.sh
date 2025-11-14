#!/bin/bash
# Build script for rust-nonprice

set -e

echo "=== Rust-NonPrice Build Script ==="
echo

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "Error: Rust/Cargo is not installed"
    echo "Please install Rust: https://rustup.rs/"
    exit 1
fi

# Build the library
echo "1. Building library..."
cargo build --lib

if [ $? -eq 0 ]; then
    echo "   ✅ Library built successfully"
else
    echo "   ❌ Library build failed"
    echo "   Please fix compilation errors first"
    exit 1
fi

# Build the CLI tool
echo
echo "2. Building CLI tool..."
cargo build --bin np-indicator

if [ $? -eq 0 ]; then
    echo "   ✅ CLI tool built successfully"
else
    echo "   ❌ CLI tool build failed"
    echo "   Please fix compilation errors first"
    exit 1
fi

# Run tests
echo
echo "3. Running tests..."
cargo test --lib

if [ $? -eq 0 ]; then
    echo "   ✅ Tests passed"
else
    echo "   ⚠️  Some tests failed"
fi

# Build Python bindings
echo
echo "4. Building Python bindings..."
if [ -d "python" ]; then
    cd python
    maturin build --release
    if [ $? -eq 0 ]; then
        echo "   ✅ Python bindings built successfully"
        echo "   Install with: pip install target/wheels/*.whl"
    else
        echo "   ⚠️  Python bindings build failed"
        echo "   Make sure maturin is installed: pip install maturin"
    fi
    cd ..
else
    echo "   ⚠️  Python directory not found, skipping"
fi

echo
echo "=== Build Complete ==="
echo
echo "Next steps:"
echo "  - Run examples: cargo run --example basic_usage"
echo "  - Run CLI: ./target/debug/np-indicator --help"
echo "  - Test Python bindings: python examples/python_demo.py"
echo
