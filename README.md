# notationChess

Move your chess pieces by writing the correct algebraic notation.

---

## About

This project allows you to play chess using standard notation (e.g., `e4`, `Nf3`, `O-O`).  
It uses **Pygame** for graphics and **Stockfish** as the chess engine.

---

## Building Stockfish (for Linux)

If the link below doesn't work, visit the official site:  
https://stockfishchess.org/download/

```bash
# Download the latest Linux build
wget https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64-avx2.tar

# Extract the files
tar -xvf stockfish-ubuntu-x86-64-avx2.tar

# Go to the source directory
cd stockfish/src

# Install build tools
sudo apt update
sudo apt install -y build-essential

# Build Stockfish
make ARCH=x86-64-modern

# Move the compiled binary into your project
cd ../../
rm -rf AI
mkdir AI
mv stockfish/src/stockfish AI/stockfish
