#include "dr_api.h"
#include "drcctlib.h"

#define DRCCTLIB_PRINTF(_FORMAT, _ARGS...) \
    DRCCTLIB_PRINTF_TEMPLATE("instr_analysis", _FORMAT, ##_ARGS)
#define DRCCTLIB_EXIT_PROCESS(_FORMAT, _ARGS...) \
    DRCCTLIB_CLIENT_EXIT_PROCESS_TEMPLATE("instr_analysis", _FORMAT, ##_ARGS)

#ifdef ARM_CCTLIB
#    define OPND_CREATE_CCT_INT OPND_CREATE_INT
#else
#    define OPND_CREATE_CCT_INT OPND_CREATE_INT32
#endif

#define TOP_REACH_NUM_SHOW 10

uint64_t *ml_hndl_call_num;
uint64_t ml_count = 0;
uint64_t *ms_hndl_call_num;
uint64_t ms_count = 0;
uint64_t *cb_hndl_call_num;
uint64_t cb_count = 0;
uint64_t *ub_hndl_call_num;
uint64_t ub_count = 0;
static file_t gTraceFile;

using namespace std;

typedef struct _output_format_t {
    context_handle_t handle;
    uint64_t count;
} output_format_t;

// Execution
void
InsCount(int32_t slot, int32_t instr_cat)
{
    // Get the context unique Id during the application runtime
    void *drcontext = dr_get_current_drcontext();
    context_handle_t cur_ctxt_hndl = drcctlib_get_context_handle(drcontext, slot);

    // Add one for the count number of the context’s instruction
    if(instr_cat == 1) {
        ml_hndl_call_num[cur_ctxt_hndl]++;
        ml_count++;
    } else if(instr_cat == 2) {
        ms_hndl_call_num[cur_ctxt_hndl]++;
        ms_count++;
    } else if(instr_cat == 3) {
        cb_hndl_call_num[cur_ctxt_hndl]++;
        cb_count++;
    } else if(instr_cat == 4) {
        ub_hndl_call_num[cur_ctxt_hndl]++;
        ub_count++;
    }
}

// Transformation
void
InsTransEventCallback(void *drcontext, instr_instrument_msg_t *instrument_msg)
{

    instrlist_t *bb = instrument_msg->bb;
    instr_t *instr = instrument_msg->instr;
    int32_t slot = instrument_msg->slot;
    int32_t instr_cat = 0;

    if(instr_reads_memory(instr)) { // memory loads
        instr_cat = 1;
    } else if(instr_writes_memory(instr)) { // memory stores
        instr_cat = 2;
    } else if(instr_is_cbr(instr)) { // conditional branches
        instr_cat = 3;
    } else if(instr_is_ubr(instr)) { // unconditional branches
        instr_cat = 4;
    }

    // check categories here and pass those to clean_call and pass map or something so that it will be present everywhere in call

    dr_insert_clean_call(drcontext, bb, instr, (void *)InsCount, false, 2, OPND_CREATE_CCT_INT(slot), OPND_CREATE_CCT_INT(instr_cat)); // 2 is number of parameters to pass to function
}

static inline void
InitGlobalBuff()
{
    ml_hndl_call_num = (uint64_t *)dr_raw_mem_alloc(
        CONTEXT_HANDLE_MAX * sizeof(uint64_t), DR_MEMPROT_READ | DR_MEMPROT_WRITE, NULL);
    if (ml_hndl_call_num == NULL) {
        DRCCTLIB_EXIT_PROCESS(
            "init_global_buff error: dr_raw_mem_alloc fail ml_hndl_call_num");
    }
    ms_hndl_call_num = (uint64_t *)dr_raw_mem_alloc(
        CONTEXT_HANDLE_MAX * sizeof(uint64_t), DR_MEMPROT_READ | DR_MEMPROT_WRITE, NULL);
    if (ms_hndl_call_num == NULL) {
        DRCCTLIB_EXIT_PROCESS(
            "init_global_buff error: dr_raw_mem_alloc fail ms_hndl_call_num");
    }
    cb_hndl_call_num = (uint64_t *)dr_raw_mem_alloc(
        CONTEXT_HANDLE_MAX * sizeof(uint64_t), DR_MEMPROT_READ | DR_MEMPROT_WRITE, NULL);
    if (cb_hndl_call_num == NULL) {
        DRCCTLIB_EXIT_PROCESS(
            "init_global_buff error: dr_raw_mem_alloc fail cb_hndl_call_num");
    }
    ub_hndl_call_num = (uint64_t *)dr_raw_mem_alloc(
        CONTEXT_HANDLE_MAX * sizeof(uint64_t), DR_MEMPROT_READ | DR_MEMPROT_WRITE, NULL);
    if (ub_hndl_call_num == NULL) {
        DRCCTLIB_EXIT_PROCESS(
            "init_global_buff error: dr_raw_mem_alloc fail ub_hndl_call_num");
    }
}

static inline void
FreeGlobalBuff()
{
    dr_raw_mem_free(ml_hndl_call_num, CONTEXT_HANDLE_MAX * sizeof(uint64_t));
    dr_raw_mem_free(ms_hndl_call_num, CONTEXT_HANDLE_MAX * sizeof(uint64_t));
    dr_raw_mem_free(cb_hndl_call_num, CONTEXT_HANDLE_MAX * sizeof(uint64_t));
    dr_raw_mem_free(ub_hndl_call_num, CONTEXT_HANDLE_MAX * sizeof(uint64_t));
}

static void
ClientInit(int argc, const char *argv[])
{
    char name[MAXIMUM_FILEPATH] = "";
    DRCCTLIB_INIT_LOG_FILE_NAME(name, "instr_analysis", "out");
    DRCCTLIB_PRINTF("Creating log file at:%s", name);

    gTraceFile = dr_open_file(name, DR_FILE_WRITE_OVERWRITE | DR_FILE_ALLOW_LARGE);
    DR_ASSERT(gTraceFile != INVALID_FILE);

    InitGlobalBuff();
    drcctlib_init(DRCCTLIB_FILTER_ALL_INSTR, INVALID_FILE, InsTransEventCallback, false);
}

static void
analyze_ml_instr(void)
{
    // Get the number of all contexts. 
    context_handle_t max_ctxt_hndl = drcctlib_get_global_context_handle_num();
    DRCCTLIB_PRINTF("Total Instructions:%d", max_ctxt_hndl);

    output_format_t *output_list = (output_format_t *)dr_global_alloc(TOP_REACH_NUM_SHOW * sizeof(output_format_t));
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        output_list[i].handle = 0;
        output_list[i].count = 0;
    }

    // Select the top contexts with the most number of instruction execute times and order them.
    for (context_handle_t i = 0; i < max_ctxt_hndl; i++) {
        if (ml_hndl_call_num[i] <= 0) {
            continue;
        }
        if (ml_hndl_call_num[i] > output_list[0].count) {
            uint64_t min_count = ml_hndl_call_num[i];
            int32_t min_idx = 0;
            for (int32_t j = 1; j < TOP_REACH_NUM_SHOW; j++) {
                if (output_list[j].count < min_count) {
                    min_count = output_list[j].count;
                    min_idx = j;
                }
            }
            output_list[0].count = min_count;
            output_list[0].handle = output_list[min_idx].handle;
            output_list[min_idx].count = ml_hndl_call_num[i];
            output_list[min_idx].handle = i;
        }
    }
    output_format_t temp;
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        for (int32_t j = i; j < TOP_REACH_NUM_SHOW; j++) {
            if (output_list[i].count < output_list[j].count) {
                temp = output_list[i];
                output_list[i] = output_list[j];
                output_list[j] = temp;
            }
        }
    }

    // Output the execution times and backtrace of the ordered top contexts
    dr_fprintf(gTraceFile, "MEMORY LOAD : %d\n", ml_count);
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        if (output_list[i].handle == 0) {
            break;
        }

        dr_fprintf(gTraceFile, "NO. %d PC ", i + 1);
        drcctlib_print_backtrace_first_item(gTraceFile, output_list[i].handle, true, false);
        dr_fprintf(gTraceFile, "=>EXECUTION TIMES\n%lld\n=>BACKTRACE\n", output_list[i].count);
        drcctlib_print_backtrace(gTraceFile, output_list[i].handle, false, true, -1);
        dr_fprintf(gTraceFile, "\n\n");
    }
    dr_global_free(output_list, TOP_REACH_NUM_SHOW * sizeof(output_format_t));

}

static void
analyze_ms_instr(void)
{
    // Get the number of all contexts. 
    context_handle_t max_ctxt_hndl = drcctlib_get_global_context_handle_num();

    output_format_t *output_list = (output_format_t *)dr_global_alloc(TOP_REACH_NUM_SHOW * sizeof(output_format_t));
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        output_list[i].handle = 0;
        output_list[i].count = 0;
    }

    // Select the top contexts with the most number of instruction execute times and order them.
    for (context_handle_t i = 0; i < max_ctxt_hndl; i++) {
        if (ms_hndl_call_num[i] <= 0) {
            continue;
        }
        if (ms_hndl_call_num[i] > output_list[0].count) {
            uint64_t min_count = ms_hndl_call_num[i];
            int32_t min_idx = 0;
            for (int32_t j = 1; j < TOP_REACH_NUM_SHOW; j++) {
                if (output_list[j].count < min_count) {
                    min_count = output_list[j].count;
                    min_idx = j;
                }
            }
            output_list[0].count = min_count;
            output_list[0].handle = output_list[min_idx].handle;
            output_list[min_idx].count = ms_hndl_call_num[i];
            output_list[min_idx].handle = i;
        }
    }
    output_format_t temp;
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        for (int32_t j = i; j < TOP_REACH_NUM_SHOW; j++) {
            if (output_list[i].count < output_list[j].count) {
                temp = output_list[i];
                output_list[i] = output_list[j];
                output_list[j] = temp;
            }
        }
    }

    // Output the execution times and backtrace of the ordered top contexts
    dr_fprintf(gTraceFile, "MEMORY STORE : %d\n", ms_count);
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        if (output_list[i].handle == 0) {
            break;
        }

        dr_fprintf(gTraceFile, "NO. %d PC ", i + 1);
        drcctlib_print_backtrace_first_item(gTraceFile, output_list[i].handle, true, false);
        dr_fprintf(gTraceFile, "=>EXECUTION TIMES\n%lld\n=>BACKTRACE\n", output_list[i].count);
        drcctlib_print_backtrace(gTraceFile, output_list[i].handle, false, true, -1);
        dr_fprintf(gTraceFile, "\n\n");
    }
    dr_global_free(output_list, TOP_REACH_NUM_SHOW * sizeof(output_format_t));
}

static void
analyze_cb_instr(void)
{
    // Get the number of all contexts. 
    context_handle_t max_ctxt_hndl = drcctlib_get_global_context_handle_num();

    output_format_t *output_list = (output_format_t *)dr_global_alloc(TOP_REACH_NUM_SHOW * sizeof(output_format_t));
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        output_list[i].handle = 0;
        output_list[i].count = 0;
    }

    // Select the top contexts with the most number of instruction execute times and order them.
    for (context_handle_t i = 0; i < max_ctxt_hndl; i++) {
        if (cb_hndl_call_num[i] <= 0) {
            continue;
        }
        if (cb_hndl_call_num[i] > output_list[0].count) {
            uint64_t min_count = cb_hndl_call_num[i];
            int32_t min_idx = 0;
            for (int32_t j = 1; j < TOP_REACH_NUM_SHOW; j++) {
                if (output_list[j].count < min_count) {
                    min_count = output_list[j].count;
                    min_idx = j;
                }
            }
            output_list[0].count = min_count;
            output_list[0].handle = output_list[min_idx].handle;
            output_list[min_idx].count = cb_hndl_call_num[i];
            output_list[min_idx].handle = i;
        }
    }
    output_format_t temp;
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        for (int32_t j = i; j < TOP_REACH_NUM_SHOW; j++) {
            if (output_list[i].count < output_list[j].count) {
                temp = output_list[i];
                output_list[i] = output_list[j];
                output_list[j] = temp;
            }
        }
    }

    // Output the execution times and backtrace of the ordered top contexts
    dr_fprintf(gTraceFile, "CONDITIONAL BRANCHES : %d\n", cb_count);
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        if (output_list[i].handle == 0) {
            break;
        }

        dr_fprintf(gTraceFile, "NO. %d PC ", i + 1);
        drcctlib_print_backtrace_first_item(gTraceFile, output_list[i].handle, true, false);
        dr_fprintf(gTraceFile, "=>EXECUTION TIMES\n%lld\n=>BACKTRACE\n", output_list[i].count);
        drcctlib_print_backtrace(gTraceFile, output_list[i].handle, false, true, -1);
        dr_fprintf(gTraceFile, "\n\n");
    }
    dr_global_free(output_list, TOP_REACH_NUM_SHOW * sizeof(output_format_t));
}

static void
analyze_ub_instr(void)
{
    // Get the number of all contexts. 
    context_handle_t max_ctxt_hndl = drcctlib_get_global_context_handle_num();

    output_format_t *output_list = (output_format_t *)dr_global_alloc(TOP_REACH_NUM_SHOW * sizeof(output_format_t));
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        output_list[i].handle = 0;
        output_list[i].count = 0;
    }

    // Select the top contexts with the most number of instruction execute times and order them.
    for (context_handle_t i = 0; i < max_ctxt_hndl; i++) {
        if (ub_hndl_call_num[i] <= 0) {
            continue;
        }
        if (ub_hndl_call_num[i] > output_list[0].count) {
            uint64_t min_count = ub_hndl_call_num[i];
            int32_t min_idx = 0;
            for (int32_t j = 1; j < TOP_REACH_NUM_SHOW; j++) {
                if (output_list[j].count < min_count) {
                    min_count = output_list[j].count;
                    min_idx = j;
                }
            }
            output_list[0].count = min_count;
            output_list[0].handle = output_list[min_idx].handle;
            output_list[min_idx].count = ub_hndl_call_num[i];
            output_list[min_idx].handle = i;
        }
    }
    output_format_t temp;
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        for (int32_t j = i; j < TOP_REACH_NUM_SHOW; j++) {
            if (output_list[i].count < output_list[j].count) {
                temp = output_list[i];
                output_list[i] = output_list[j];
                output_list[j] = temp;
            }
        }
    }

    // Output the execution times and backtrace of the ordered top contexts
    dr_fprintf(gTraceFile, "UNCONDITIONAL BRANCHES : %d\n", ub_count);
    for (int32_t i = 0; i < TOP_REACH_NUM_SHOW; i++) {
        if (output_list[i].handle == 0) {
            break;
        }

        dr_fprintf(gTraceFile, "NO. %d PC ", i + 1);
        drcctlib_print_backtrace_first_item(gTraceFile, output_list[i].handle, true, false);
        dr_fprintf(gTraceFile, "=>EXECUTION TIMES\n%lld\n=>BACKTRACE\n", output_list[i].count);
        drcctlib_print_backtrace(gTraceFile, output_list[i].handle, false, true, -1);
        dr_fprintf(gTraceFile, "\n\n");
    }
    dr_global_free(output_list, TOP_REACH_NUM_SHOW * sizeof(output_format_t));
}

static void
ClientExit(void)
{
    analyze_ml_instr(); // For Machine Load
    analyze_ms_instr(); // For Machine Store
    analyze_cb_instr(); // For Conditional Branch
    analyze_ub_instr(); // For Unconditional Branch
    FreeGlobalBuff();
    drcctlib_exit();
    dr_close_file(gTraceFile);
}

#ifdef __cplusplus
extern "C" {
#endif

DR_EXPORT void
dr_client_main(client_id_t id, int argc, const char *argv[])
{
    dr_set_client_name("DynamoRIO Client 'instr_analysis'", "http://dynamorio.org/issues");
    ClientInit(argc, argv);
    dr_register_exit_event(ClientExit);
}

#ifdef __cplusplus
}
#endif