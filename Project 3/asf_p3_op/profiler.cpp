
#include <iostream>
#include <bitset>
#include <cstdint>
#include <cmath>
#include "profiler.h"
#include "drcctlib_vscodeex_format.h"

using namespace std;
using namespace DrCCTProf;

/*
    Tips: different integer types have distinct boundaries
    INT64_MAX, INT32_MAX, INT16_MAX, INT8_MAX
    INT64_MIN, INT32_MIN, INT16_MIN, INT8_MIN
*/

namespace runtime_profiling {

    static inline int64_t
    GetOpndIntValue(Operand opnd)
    {
        if (opnd.type == OperandType::kImmediateFloat ||
            opnd.type == OperandType::kImmediateDouble ||
            opnd.type == OperandType::kUnsupportOpnd || opnd.type == OperandType::kNullOpnd) {
            return 0;
        }
        int64_t value = 0;
        switch (opnd.size) {
        case 1: value = static_cast<int64_t>(opnd.value.valueInt8); break;
        case 2: value = static_cast<int64_t>(opnd.value.valueInt16); break;
        case 4: value = static_cast<int64_t>(opnd.value.valueInt32); break;
        case 8: value = static_cast<int64_t>(opnd.value.valueInt64); break;
        default: break;
        }
        return value;
    }

    // implement your algorithm in this function
    static inline bool
    IntegerOverflow(Instruction *instr, uint64_t flagsValue)
    {
        int64_t a = GetOpndIntValue(instr->getSrcOperand(0));
        int64_t b = GetOpndIntValue(instr->getSrcOperand(1));
        int64_t c = GetOpndIntValue(instr->getDstOperand(0));
        int64_t maxim = INT64_MAX;
        int64_t minim = INT64_MAX;
        switch(instr->getDstOperand(0).size) {
            case 1: maxim = INT8_MAX; minim = INT8_MIN; break;
            case 2: maxim = INT16_MAX; minim = INT16_MIN; break;
            case 4: maxim = INT32_MAX; minim = INT32_MIN; break;
            case 8: maxim = INT64_MAX; minim = INT64_MIN; break;
            default: maxim = INT_MAX; minim = INT_MIN; break;
        }

        if (instr->getOperatorType() == OperatorType::kOPadd) {
            if (a > maxim || a < minim || b > maxim || b < minim)
                return true;
            else if (a >= 0 && b >= 0 && b > maxim - a)
                return true;
            else if (a < 0 && b < 0 && b < minim - a)
                return true;
            return false;
        }
        else if (instr->getOperatorType() == OperatorType::kOPsub) {
            if (a > maxim || a < minim || b > maxim || b < minim)
                return true;
            else if (a >= 0 && b < a - maxim)
                return true;
            else if (a < 0 && b > a - minim)
                return true;
            return false;
        }
        else if (instr->getOperatorType() == OperatorType::kOPshl) {

            if (a > maxim || a < minim || b > maxim || b < minim)
                return true;
            else if (a >= 0 && a >= maxim / pow(2, b))
                return true;
            else if (a < 0 && a < minim / pow(2, b))
                return true;
            return false;
        }

        return false;
    }

    void
    OnAfterInsExec(Instruction *instr, context_handle_t contxt, uint64_t flagsValue,
                            CtxtContainer *ctxtContainer)
    {
        if (IntegerOverflow(instr, flagsValue)) {
            // cout << "\n ** overflow happened ** \n";
            ctxtContainer->addCtxt(contxt);
        }
        // add: Destination = Source0 + Source1
        if (instr->getOperatorType() == OperatorType::kOPadd) {
            Operand srcOpnd0 = instr->getSrcOperand(0);
            Operand srcOpnd1 = instr->getSrcOperand(1);
            Operand dstOpnd = instr->getDstOperand(0);
            std::bitset<64> bitFlagsValue(flagsValue);

            cout << "ip(" << hex << instr->ip << "):"
                << "add " << dec << GetOpndIntValue(srcOpnd0) << " "
                << GetOpndIntValue(srcOpnd1) << " -> " << GetOpndIntValue(dstOpnd) << " "
                << bitFlagsValue << endl;
        }
        // sub: Destination = Source0 - Source1
        if (instr->getOperatorType() == OperatorType::kOPsub) {
            Operand srcOpnd0 = instr->getSrcOperand(0);
            Operand srcOpnd1 = instr->getSrcOperand(1);
            Operand dstOpnd = instr->getDstOperand(0);
            
            std::bitset<64> bitFlagsValue(flagsValue);

            cout << "ip(" << hex << instr->ip << "):"
                << "sub " << dec << GetOpndIntValue(srcOpnd0) << " "
                << GetOpndIntValue(srcOpnd1) << " -> " << GetOpndIntValue(dstOpnd) << " "
                << bitFlagsValue << endl;
        }
        // shl: Destination = Source0 << Source1
        if (instr->getOperatorType() == OperatorType::kOPshl) {
            Operand srcOpnd0 = instr->getSrcOperand(0);
            Operand srcOpnd1 = instr->getSrcOperand(1);
            Operand dstOpnd = instr->getDstOperand(0);
            std::bitset<64> bitFlagsValue(flagsValue);

            cout << "ip(" << hex << instr->ip << "):"
                << "shl " << dec << GetOpndIntValue(srcOpnd0) << " "
                << GetOpndIntValue(srcOpnd1) << " -> " << GetOpndIntValue(dstOpnd) << " "
                << bitFlagsValue << endl;
        }
    }

    void
    OnBeforeAppExit(CtxtContainer *ctxtContainer)
    {
        Profile::profile_t *profile = new Profile::profile_t();
        profile->add_metric_type(1, "", "integer overflow occurrence");

        std::vector<context_handle_t> list = ctxtContainer->getCtxtList();
        for (size_t i = 0; i < list.size(); i++) {
            inner_context_t *cur_ctxt = drcctlib_get_full_cct(list[i]);
            profile->add_sample(cur_ctxt)->append_metirc((uint64_t)1);
            drcctlib_free_full_cct(cur_ctxt);
        }
        profile->serialize_to_file("integer-overflow-profile.drcctprof");
        delete profile;

        file_t profileTxt = dr_open_file("integer-overflow-profile.txt", DR_FILE_WRITE_OVERWRITE | DR_FILE_ALLOW_LARGE);
        DR_ASSERT(profileTxt != INVALID_FILE);
        for (size_t i = 0; i < list.size(); i++) {
            dr_fprintf(profileTxt, "INTEGER OVERFLOW\n");
            drcctlib_print_backtrace_first_item(profileTxt, list[i], true, false);
            dr_fprintf(profileTxt, "=>BACKTRACE\n");
            drcctlib_print_backtrace(profileTxt, list[i], false, true, -1);
            dr_fprintf(profileTxt, "\n\n");
        }
        dr_close_file(profileTxt);
    }

}