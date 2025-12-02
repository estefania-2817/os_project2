#!/bin/bash

echo "===================================="
echo "::::: DECODER IMAGE TESTS :::::"
echo "===================================="

# --- Colores y configuración ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
OS_NAME=$(uname -s)

# --- Variables Globales de Puntuación ---
TOTAL_TESTS=6
PASSED_TESTS=0

# --- Nombres de archivos y directorios (ajusta si es necesario) ---
C_SRC_FILE="../decode_c/src/main.c"
C_BINARY="decode_c"
PYTHON_SCRIPT="../decode_py/main.py"


# ==============================================================================
# FUNCIÓN PRINCIPAL DE TESTS
# Argumento: "c" o "py"
# ==============================================================================
run_decoder_tests() {
    local implementation=$1
    local PID=0
    
    echo "------------------------------------"
    echo "--- Running tests for: ${implementation^^}"
    echo "------------------------------------"

    rm -f ./outputs/output_*.ppm ./outputs/output_*.txt "$C_BINARY"

    # --- Ejecución del Programa ---
    if [ "$implementation" = "c" ]; then
        echo "Compiling C program..."
        if ! gcc "$C_SRC_FILE" -o "$C_BINARY" -pthread; then
            echo -e "${RED}❌ C Compilation failed. Skipping C tests.${NC}"
            return
        fi
        # Lanzar en segundo plano y capturar PID
        ./"$C_BINARY" > /dev/null 2>&1 &
        PID=$!
    elif [ "$implementation" = "py" ]; then
        # Lanzar en segundo plano y capturar PID
        python3 "$PYTHON_SCRIPT" > /dev/null 2>&1 &
        PID=$!
    fi

    echo "Program ($implementation) launched with PID: $PID. Waiting a few seconds for it to work..."
    

    # ========== TESTS DE VERIFICACIÓN ==========

    # --- Test 1: Verificar que se crearon los 4 hilos ---
    echo -e "${YELLOW}1. VERIFY THREAD CREATION${NC}"
    
    local thread_count=0
    case "$OS_NAME" in
        Linux)
            if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
                thread_count=$(ps -o nlwp= -p "$PID" | tr -d ' ')
                echo "   (DEBUG: Process $PID is alive. Found $thread_count threads/tasks)"
            else
                echo "   (DEBUG: Process $PID was not found after the wait period)"
            fi

            # El proceso principal (1) + 4 hilos = 5
            if [ "${thread_count:-0}" -eq 5 ]; then
                 echo -e "   ${GREEN} PASSED - Detected exactly 5 tasks (1 main + 4 worker threads).${NC}"
                 PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                 echo -e "   ${RED} FAILED - Expected 5 threads/tasks, but detected $thread_count.${NC}"
            fi
            ;;
        Darwin|*)
            # Para otros SO, nos basamos en los archivos creados.
            local files_created=$(ls output_*.ppm 2>/dev/null | wc -l)
            if [ "$files_created" -eq 4 ]; then
                echo -e "   ${GREEN} PASSED - 4 PPM files created, indicating 4 threads ran successfully.${NC}"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                echo -e "   ${RED} FAILED - Expected 4 PPM files for 4 threads, but found $files_created.${NC}"
            fi
            ;;
    esac
    sleep 1
    # Limpieza: Asegurarse de que el proceso en segundo plano se termine.
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null; then
        kill -9 "$PID" 2>/dev/null
    fi
    wait "$PID" 2>/dev/null # Limpia el proceso zombie si lo hubiera

    # --- Test 2: Validar colores del test CORRECTO (clave 88) ---
    echo -e "${YELLOW}2. VALIDATE CORRECT DECODING (Key 88)${NC}"

    FILE_88="./outputs/output_88.txt"
    if [ -f "$FILE_88" ]; then
        # -F para cadena fija, -c para contar.
        # IMPORTANTE: Los colores del generador C y Python deben ser idénticos.
        # El generador C crea la cara amarilla (255,255,0), fondo verde (20,180,20) y ojos negros (0,0,0)
        local contains_c1=$(grep -cF "20 180 20" "$FILE_88")
        local contains_c2=$(grep -cF "255 255 0" "$FILE_88")
        local contains_c3=$(grep -cF "0 0 0" "$FILE_88")

        if [ "$contains_c1" -gt 0 ]&& [ "$contains_c2" -gt 0 ]&& [ "$contains_c3" -gt 0 ]; then
            echo -e "   ${GREEN} PASSED - Found expected original colors in $FILE_88.${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "   ${RED} FAILED - Did not find all expected colors in $FILE_88.${NC}"
            echo "     (Expected '20 180 20', '255 255 0', '0 0 0')"
        fi
    else
        echo -e "   ${RED} FAILED - File $FILE_88 not found.${NC}"
    fi

    # --- Test 3: Validar colores de un test INCORRECTO (clave 222) ---
    echo -e "${YELLOW}3. VALIDATE INCORRECT DECODING (Key 222)${NC}"
    FILE_222="./outputs/output_222.txt"
    if [ -f "$FILE_222" ]; then
        local contains_c1=$(grep -cF "20 180 20" "$FILE_222")
        local contains_c2=$(grep -cF "255 255 0" "$FILE_222")
        
        if [ "$contains_c1" -eq 0 ] && [ "$contains_c2" -eq 0 ]; then
            echo -e "   ${GREEN} PASSED - File $FILE_222 correctly does not contain original colors.${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "   ${RED} FAILED - File $FILE_222 should not contain original colors, but it does.${NC}"
        fi
    else
        echo -e "   ${RED} FAILED - File $FILE_222 not found.${NC}"
    fi
}

# ==============================================================================
# EJECUCIÓN DE LOS BLOQUES DE TEST
# ==============================================================================

# --- Ejecutar para C ---
run_decoder_tests "c"
sleep 1
run_decoder_tests "py"


# ==============================================================================
# REPORTE FINAL
# ==============================================================================
echo "===================================="
echo "FINAL RESULT:"
echo "===================================="


PERCENTAGE=$((PASSED_TESTS * 100 / TOTAL_TESTS))


# Elige el umbral de calificación que prefieras
if [ $PERCENTAGE -ge 95 ]; then
    echo -e "${GREEN}Tests passed: $PASSED_TESTS/$TOTAL_TESTS ($PERCENTAGE%)${NC}"
    echo -e "${GREEN}EXCELLENT! All decoding tests passed.${NC}"
    exit 0
elif [ $PERCENTAGE -ge 70 ]; then
    echo -e "${YELLOW}Tests passed: $PASSED_TESTS/$TOTAL_TESTS ($PERCENTAGE%)${NC}"
    echo -e "${YELLOW}  REGULAR - Some tests failed.${NC}"
    exit 1
else
    echo -e "${RED}Tests passed: $PASSED_TESTS/$TOTAL_TESTS ($PERCENTAGE%)${NC}"
    echo -e "${RED} DEFICIENT - Most tests failed.${NC}"
    exit 2
fi
