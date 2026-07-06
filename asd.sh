wget https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64-avx2.tar
tar -xvf stockfish-ubuntu-x86-64-avx2.tar

cd stockfish/src

sudo apt update
sudo apt install build-essential

make build ARCH=x86-64-modern

cd ../../
rm -rf AI
mkdir AI
mv stockfish/src/stockfish AI/stockfish

