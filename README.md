# Pompeiu-Hausdorff Distance: Extensão com Busca em Profundidade Iterativa (IDA*)

Este repositório contém uma extensão acadêmica do projeto **pompeiu_hausdorff**, originalmente desenvolvido por **Leonardo Sacht** e **Alec Jacobson** para o artigo *"Cascading upper bounds for triangle soup Pompeiu-Hausdorff distance"* (Symposium on Geometry Processing - SGP 2024).

O objetivo desta extensão é investigar e implementar uma alternativa de busca com **uso limitado de memória** baseada em **Iterative Deepening Branch-and-Bound (IDA*)**, mantendo as mesmas garantias de certificação numérica $[l, u_{\max}]$ sob tolerância $\varepsilon$, e disponibilizar uma suíte automatizada de instrumentação para comparação empírica de consumo de memória RAM (Peak RSS) e tempo de execução em relação ao algoritmo original (*Best-First Search*).

---

## Autoria Original e Referência

Todo o núcleo matemático de limitantes geométricos em cascata ($u_0, u_1, u_2, u_3, u_4$), a construção de BVH (AABB Tree via `libigl`) e o algoritmo de referência (*Best-First Search*) pertencem aos autores originais:

* **Autores Originais:** Leonardo Sacht e Alec Jacobson
* **Artigo:** *Cascading upper bounds for triangle soup Pompeiu-Hausdorff distance* (Computer Graphics Forum / SGP, 2024)
* **Repositório Oficial:** [https://github.com/leokollersacht/pompeiu_hausdorff](https://github.com/leokollersacht/pompeiu_hausdorff)

Caso utilize a base original em trabalhos acadêmicos, cite os autores originais:

```bibtex
@article{sacht2024cascading,
  title={Cascading upper bounds for triangle soup Pompeiu-Hausdorff distance},
  author={Sacht, Leonardo and Jacobson, Alec},
  journal={Computer Graphics Forum},
  year={2024}
}
```

---

## Diferencial e Principais Modificações

No algoritmo original, a subdivisão adaptativa da malha $A$ é guiada por uma **fila de prioridades global** (*Best-First Search*). Embora eficiente em número de subdivisões, a fila de prioridades retém na memória principal todos os sub-triângulos ativos pendentes de refinamento, o que pode gerar alto consumo de memória RAM em malhas densas ou sob tolerâncias $\varepsilon$ muito restritas.

As principais modificações introduzidas neste projeto são:

1. **Motor de Busca com Memória Limitada (`IDAStarEngine`):**
   * Implementação da classe `phd::search::IDAStarEngine` (`src/IDAStarEngine.h`, `src/IDAStarEngine.cpp`) utilizando busca em profundidade iterativa com limiar dinâmico (*Iterative Deepening Branch-and-Bound*).
   * A pilha de execução cresce apenas com a profundidade da árvore de subdivisão, reduzindo significativamente o pico de memória residente (Peak RSS) em comparação com a fila de prioridades global.
   * Preservação do critério de parada certificado $(u_{\max} - l) \le \varepsilon_{\text{scaled}}$.

2. **Modularização da Arquitetura de Busca:**
   * Extração da interface abstrata `phd::search::DistanceSearchEngine` (`src/DistanceSearchEngine.h`), isolando a estratégia de exploração (`BestFirstEngine` vs. `IDAStarEngine`) do cálculo dos limitantes geométricos (`src/geometric_bounds.cpp`) e da subdivisão de triângulos (`src/subdivision.cpp`).

3. **Telemetria de Execução (`src/telemetry.h`, `src/telemetry.cpp`):**
   * Contabilização detalhada de `subdivided_faces` e número de avaliações de cada estágio da cascata de limitantes (`u0_calls` até `u4_calls`), além dos tempos de BVH e busca (`bvh_time(ms)`, `bound_time(ms)`).

4. **Suíte de Profiling e Benchmark Comparativo (`benchmarks/`):**
   * `benchmarks/profile_runner.py`: executor isolado que monitora o processo via `/proc/[pid]/status` (`VmHWM`/`VmRSS` em intervalos configuráveis) e `getrusage`, medindo Peak RSS, tempo de parede, tempo de CPU e exportando resultados para CSV.
   * `benchmarks/compare_engines.py`: script comparativo que executa `best_first` e `idastar` sobre o mesmo par de malhas, calcula os deltas percentuais de memória, tempo e chamadas de limitantes, e valida a convergência/paridade numérica entre ambos os motores.

5. **Compatibilidade com Compiladores Modernos:**
   * Inclusão explícita de `<iomanip>` em `main.cpp` para corrigir erro de compilação com `std::setprecision` em versões recentes do GCC (GCC 12+) e Clang.

---

## Estrutura do Repositório

```text
.
├── CMakeLists.txt              # Configuração de build CMake (libphd, executável e bindings)
├── main.cpp                    # Interface CLI em C++ com seleção de motor de busca
├── cmake/                      # Módulos CMake (FetchContent para libigl v2.5.0 e Eigen)
├── src/
│   ├── DistanceSearchEngine.h  # Interface comum dos motores de busca e SearchContext
│   ├── BestFirstEngine.*       # Motor baseline (fila de prioridades)
│   ├── IDAStarEngine.*         # Motor proposto (IDA* / IDB&B com memória limitada)
│   ├── geometric_bounds.*      # Limitantes geométricos em cascata (u0..u4)
│   ├── subdivision.*           # Rotinas de subdivisão de triângulos
│   ├── telemetry.*             # Coleta de métricas internas da busca
│   ├── PompeiuHausdorff.*      # Orquestrador principal e construção da AABB tree
│   └── bindings.cpp            # Bindings Python via nanobind
├── benchmarks/
│   ├── profile_runner.py       # Profiling de Peak RSS e CPU/Wall time (Linux)
│   └── compare_engines.py      # Comparação automatizada Best-First vs. IDA*
├── meshes/                     # Malhas .obj de teste
└── tests/
    └── test.py                 # Teste de integração dos bindings Python
```

---

## Guia Passo a Passo: Compilação e Execução

### 1. Pré-requisitos

* Sistema operacional Linux (necessário para leitura de `/proc/[pid]/status` nos scripts de profiling)
* Compilador C++ compatível (GCC ou Clang)
* `cmake` (>= 3.16) e `make` ou `ninja`
* `git` (o CMake baixa automaticamente o `libigl` v2.5.0 e o `Eigen` via `FetchContent`)
* `python3` (>= 3.8) para os scripts de benchmark e testes

Exemplo de instalação das ferramentas de build no Ubuntu/Debian ou Arch/CachyOS:

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y build-essential cmake git python3

# Arch Linux / CachyOS
sudo pacman -S --needed base-devel cmake git python
```

### 2. Compilação em Modo Release

Na raiz do repositório:

```bash
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
```

O executável será gerado em `build/pompeiu_hausdorff`.

---

### 3. Executando o Binário C++ Diretamente

#### Sintaxe da CLI

```bash
./build/pompeiu_hausdorff <meshA.obj> <meshB.obj> <tol> <max_factor> <normalize> [engine]
```

**Parâmetros:**
* `meshA.obj`: caminho para a malha/sopa de triângulos $A$ no formato `.obj`.
* `meshB.obj`: caminho para a malha/sopa de triângulos $B$ no formato `.obj`.
* `tol`: tolerância máxima desejada entre o limitante superior e o inferior ($u_{\max} - l$).
* `max_factor`: fator multiplicativo limite para o número de faces e vértices na subdivisão de $A$.
* `normalize`: `1` para normalizar a tolerância pela diagonal da bounding box de $A$ ($d_A$), ou `0` para usar tolerância absoluta.
* `engine` *(opcional)*: motor de busca utilizado — `best_first` (padrão) ou `idastar`.

> **Nota sobre o código de retorno:** mantendo a convenção do código original dos autores, o binário retorna `1` em execuções bem-sucedidas e `0` em caso de erro nos argumentos ou leitura de malha.

#### Exemplos de Execução

**Rodando o baseline original (`best_first`):**

```bash
./build/pompeiu_hausdorff meshes/107100.obj meshes/107100_sf.obj 1e-4 1000000 1 best_first
```

**Rodando a variante proposta com memória limitada (`idastar`):**

```bash
./build/pompeiu_hausdorff meshes/107100.obj meshes/107100_sf.obj 1e-4 1000000 1 idastar
```

**Saída esperada (inclui distância certificada, tempos e telemetria):**

```text
Computing Pompeiu-Hausdorff distance...
Done.
----- Results -----
dA = ...
lower=...
upper_max=...
lower/dA=...
upper_max/dA=...
bvh_time(ms)=...
bound_time(ms)=...
subdivided_faces=...
u0_calls=...
u1_calls=...
u2_calls=...
u3_calls=...
u4_calls=...
----------------------------------------
```

---

### 4. Executando Benchmarks Comparativos e Profiling

#### A. Comparação Direta (`best_first` vs. `idastar`)

O script `benchmarks/compare_engines.py` executa ambos os motores de forma isolada sobre o mesmo par de malhas, exibe uma tabela comparativa no terminal e pode exportar relatórios em Markdown e CSV:

```bash
python3 benchmarks/compare_engines.py \
  --mesh-a meshes/107100.obj \
  --mesh-b meshes/107100_sf.obj \
  --tol 1e-4 \
  --output-md relatorio_comparativo.md \
  --output-csv resultados_comparativos.csv
```

Opções principais do `compare_engines.py`:
* `--executable`: caminho para o binário (padrão: `build/pompeiu_hausdorff`).
* `--mesh-a`, `--mesh-b`: caminhos para as malhas `.obj`.
* `--tol`: tolerância de parada (padrão: `1e-4`).
* `--max-factor`: fator máximo de subdivisão (padrão: `1000000`).
* `--normalize`: normalização por $d_A$ (`1` ou `0`, padrão: `1`).
* `--output-md`: caminho opcional para salvar a tabela comparativa em Markdown.
* `--output-csv`: caminho opcional para acrescentar uma linha com os deltas no arquivo CSV.
* `--quiet`: suprime a saída intermediária de cada execução individual.

#### B. Profiling Individual de Memória e Tempo

Para coletar múltiplas execuções de um único motor em CSV (por exemplo, para análise estatística de Peak RSS):

```bash
python3 benchmarks/profile_runner.py \
  --mesh-a meshes/107100.obj \
  --mesh-b meshes/107100_sf.obj \
  --tol 1e-4 \
  --engine idastar \
  --runs 3 \
  --output-csv results_preliminar.csv
```

---

### 5. Testes e Bindings Python (Opcional)

O projeto mantém compatibilidade com os bindings Python originais via `nanobind` e `scikit-build-core`. Para compilar o módulo Python localmente e executar o teste em `tests/test.py`:

```bash
# Instalar dependências Python de teste e leitura de malhas
pip install pytest numpy libigl

# Instalar o pacote a partir do código-fonte local
pip install .

# Executar o teste de integração
pytest tests/test.py -s
```
