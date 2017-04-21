from __future__ import absolute_import
from __future__ import print_function

import veriloggen.core.vtypes as vtypes


def FixedInput(m, name, width=32, point=0,
               length=None, signed=True):
    obj = _FixedInput(width=width, length=length, signed=signed,
                      name=name, module=m, point=point)
    m.add_object(obj)
    return obj


def FixedOutput(m, name, width=32, point=0,
                length=None, signed=True):
    obj = _FixedOutput(width=width, length=length, signed=signed,
                       name=name, module=m, point=point)
    m.add_object(obj)
    return obj


def FixedInout(m, name, width=32, point=0,
               length=None, signed=True):
    obj = _FixedInout(width=width, length=length, signed=signed,
                      name=name, module=m, point=point)
    m.add_object(obj)
    return obj


def FixedReg(m, name, width=32, point=0,
             length=None, signed=True, initval=None):
    obj = _FixedReg(width=width, length=length, signed=signed, initval=initval,
                    name=name, module=m, point=point)
    m.add_object(obj)
    return obj


def FixedWire(m, name, width=32, point=0,
              length=None, signed=True):
    obj = _FixedWire(width=width, length=length, signed=signed,
                     name=name, module=m, point=point)
    m.add_object(obj)
    return obj


def FixedConst(value, point=0, signed=True, raw=False):
    obj = _FixedInt(value, point=point, raw=raw, signed=signed)
    return obj


def to_fixed(value, point):
    if point < 0:
        raise ValueError('point must be more than 0')

    if point == 0:
        return value

    if isinstance(value, (int, bool, float)) and isinstance(point, int):
        mag = 2 ** point
        return int(value * mag)

    if isinstance(value, (int, bool)):
        mag = vtypes.Int(2) ** point
        return vtypes.Int(value) * mag

    if isinstance(value, float):
        mag = vtypes.Int(2) ** point
        return vtypes.Float(value) * mag

    signed = vtypes.get_signed(value)
    return shift_left(value, point, signed)


def fixed_to_int(value, point):
    if point < 0:
        raise ValueError('point must be more than 0')

    if point == 0:
        return value

    if isinstance(value, (int, bool, float)) and isinstance(point, int):
        mag = 2 ** point
        return int(value / mag)

    if isinstance(value, (int, bool, float)):
        mag = vtypes.Int(2) ** point
        return vtypes.Int(value) / mag

    signed = vtypes.get_signed(value)
    return shift_right(value, point, signed)


def fixed_to_int_low(value, point):
    if point < 0:
        raise ValueError('point must be more than 0')

    if point == 0:
        return 0

    if isinstance(value, (int, bool, float)) and isinstance(point, int):
        mag = 2 ** point
        return int(value % mag)

    return vtypes.And(value, vtypes.Repeat(vtypes.Int(1, 1), point))


def fixed_to_real(value, point):
    if point < 0:
        raise ValueError('point must be more than 0')

    if point == 0:
        return vtypes.SystemTask('itor', value)

    if isinstance(value, float):
        raise TypeError("value is already float.")

    if isinstance(value, (int, bool)) and isinstance(point, int):
        mag = 2 ** point
        return float(value) / mag

    signed = vtypes.get_signed(value)

    width = value.bit_length()
    msb = (value[width - 1] if isinstance(value, vtypes._Variable) else
           (value >> (width - 1)) & 0x1)

    v0 = (vtypes.SystemTask('itor', fixed_to_int(value, point)) +
          vtypes.SystemTask('itor', fixed_to_int_low(value, point)) /
          vtypes.SystemTask('itor', vtypes.Int(2) ** point))

    nv = vtypes.Unot(value) + 1
    v1 = ((vtypes.SystemTask('itor', fixed_to_int(nv, point)) +
           vtypes.SystemTask('itor', fixed_to_int_low(nv, point)) /
           vtypes.SystemTask('itor', vtypes.Int(2) ** point))) * vtypes.SystemTask('itor', -1)

    return vtypes.Mux(signed and msb == 0, v0, v1)


def to_signed(value):
    if isinstance(value, int):
        return vtypes.Int(value, signed=True)
    if isinstance(value, vtypes.Int):
        return vtypes.Int(value.value, signed=True)
    if vtypes.get_signed(value):
        return value
    data = vtypes.SystemTask('signed', value)
    point = value.point if hasattr(value, 'point') else 0
    return _FixedSkipUnaryOperator(data, point, True)


def adjust(left, right, lpoint, rpoint, signed=True):
    diff_lpoint = 0 if rpoint < lpoint else rpoint - lpoint
    diff_rpoint = 0 if lpoint < rpoint else lpoint - rpoint
    ldata = left if diff_lpoint == 0 else shift_left(left, diff_lpoint, signed)
    rdata = right if diff_rpoint == 0 else shift_left(
        right, diff_rpoint, signed)
    _ldata = to_signed(ldata) if signed and diff_lpoint != 0 else ldata
    _rdata = to_signed(rdata) if signed and diff_rpoint != 0 else rdata
    return _ldata, _rdata


def shift_left(value, size, signed=True):
    if isinstance(value, vtypes.Int):
        value = value.value

    if isinstance(value, int) and isinstance(size, int):
        return value << size

    if isinstance(value, bool) and isinstance(size, int):
        return value << size

    return vtypes.Sll(value, size)


def shift_right(value, size, signed=True):
    if isinstance(value, vtypes.Int):
        value = value.value

    if isinstance(value, int) and isinstance(size, int):
        return value >> size

    if isinstance(value, bool) and isinstance(size, int):
        return value >> size

    if signed:
        return vtypes.Sra(value, size)

    return vtypes.Srl(value, size)


def _max_mux(a, b):
    return vtypes.Mux(a > b, a, b)


def _min_mux(a, b):
    return vtypes.Mux(a < b, a, b)


class _FixedBase(object):
    ast_name = None

    @property
    def int_part(self):
        return self >> self.point

    @property
    def dec_part(self):
        mask = vtypes.Mux(self.point == 0, 0, vtypes.Repeat(
            vtypes.Int(1, width=1), self.point))
        return self & mask

    def _adjust(self, value):
        lpoint = self.point
        rvalue = value
        rsigned = vtypes.get_signed(value)
        if not isinstance(value, _FixedBase):
            rpoint = 0
        else:
            rpoint = value.point

        ldiff = vtypes.Mux(lpoint <= rpoint, 0, lpoint - rpoint)
        rdiff = vtypes.Mux(lpoint >= rpoint, 0, rpoint - lpoint)
        v = vtypes.Mux(lpoint > rpoint, shift_left(rvalue, ldiff, rsigned),
                       vtypes.Mux(lpoint < rpoint, shift_right(rvalue, rdiff, rsigned), rvalue))

        return v

    @property
    def raw(self):
        width = self.width if self.width is not None else 1
        return self[0:width]

    def __lt__(self, r):
        return _FixedLessThan(self, r)

    def __le__(self, r):
        return _FixedLessEq(self, r)

    def __eq__(self, r):
        return _FixedEq(self, r)

    def __ne__(self, r):
        return _FixedNotEq(self, r)

    def __ge__(self, r):
        return _FixedGreaterEq(self, r)

    def __gt__(self, r):
        return _FixedGreaterThan(self, r)

    def __add__(self, r):
        return _FixedPlus(self, r)

    def __sub__(self, r):
        return _FixedMinus(self, r)

    def __mul__(self, r):
        return _FixedTimes(self, r)

    def __div__(self, r):
        return _FixedDivide(self, r)

    def __truediv__(self, r):
        return _FixedDivide(self, r)

    def __neg__(self):
        return _FixedUminus(self)

    def __pos__(self):
        return _FixedUplus(self)


class _FixedVariable(_FixedBase, vtypes._Variable):
    ast_name = None

    def __init__(self, width=1, length=None, signed=True, value=None, initval=None, name=None,
                 module=None, point=0):
        self.point = point
        if initval is not None and not isinstance(initval, _FixedConstant):
            initval = to_fixed(initval, point)
        vtypes._Variable.__init__(
            self, width, length, signed, value, initval, name, module)

    def write(self, value, blk=False, ldelay=None, rdelay=None):
        v = self._adjust(value)
        return vtypes._Variable.write(self, v, blk=blk, ldelay=ldelay, rdelay=rdelay)

    def write_raw(self, value, blk=False, ldelay=None, rdelay=None):
        return vtypes._Variable.write(self, value, blk=blk, ldelay=ldelay, rdelay=rdelay)

    def assign(self, value):
        v = self._adjust(value)
        return vtypes._Variable.assign(v)

    def connect(self, value):
        v = self._adjust(value)
        return vtypes._Variable.connect(v)


class _FixedInput(_FixedVariable, vtypes.Input):
    ast_name = 'Input'


class _FixedOutput(_FixedVariable, vtypes.Output):
    ast_name = 'Output'


class _FixedInout(_FixedVariable, vtypes.Inout):
    ast_name = 'Inout'


class _FixedReg(_FixedVariable, vtypes.Reg):
    ast_name = 'Reg'

    def assign(self, value):
        return vtypes.Reg.assign(self, value)

    def reset(self):
        return vtypes.Reg.reset(self, value)


class _FixedWire(_FixedVariable, vtypes.Wire):
    ast_name = 'Wire'

    def _add_subst(self, s):
        return vtypes.Wire._add_subst(self, s)


class _FixedBinaryOperator(_FixedBase, vtypes._BinaryOperator):
    ast_name = None
    overwrite_signed = False

    def init(self, left, right):
        lpoint = left.point if isinstance(left, _FixedBase) else 0
        rpoint = right.point if isinstance(right, _FixedBase) else 0
        lsigned = vtypes.get_signed(left)
        rsigned = vtypes.get_signed(right)
        point = _max_mux(lpoint, rpoint)
        signed = lsigned and rsigned if not self.overwrite_signed else False
        ldata, rdata = adjust(left, right, lpoint, rpoint, signed)
        self.point = point
        return ldata, rdata


class _FixedUnaryOperator(_FixedBase, vtypes._UnaryOperator):
    ast_name = None

    def __init__(self, right):
        vtypes._UnaryOperator.__init__(self, right)
        self.point = right.point if isinstance(right, _FixedBase) else 0


class _FixedSkipUnaryOperator(_FixedUnaryOperator, vtypes._SkipUnaryOperator):
    ast_name = '_SkipUnaryOperator'

    def __init__(self, right, point=None, signed=None):
        vtypes._SkipUnaryOperator.__init__(self, right)
        self.point = point if point is not None else 0
        self.signed = signed if signed is not None else True


class _FixedTimes(_FixedSkipUnaryOperator):
    ast_name = '_SkipUnaryOperator'
    overwrite_signed = False

    def __init__(self, left, right):
        lpoint = left.point if isinstance(left, _FixedBase) else 0
        rpoint = right.point if isinstance(right, _FixedBase) else 0
        lsigned = vtypes.get_signed(left)
        rsigned = vtypes.get_signed(right)
        point = _max_mux(lpoint, rpoint)
        signed = lsigned and rsigned if not self.overwrite_signed else False
        ldata = to_signed(left) if signed else left
        rdata = to_signed(right) if signed else right
        shift_size = _min_mux(lpoint, rpoint)
        data = vtypes.Times(ldata, rdata)
        if signed:
            data = vtypes.Sra(data, shift_size)
        else:
            data = vtypes.Srl(data, shift_size)
        _FixedSkipUnaryOperator.__init__(self, data, point, signed)


class _FixedDivide(_FixedSkipUnaryOperator):
    ast_name = '_SkipUnaryOperator'
    overwrite_signed = False

    def __init__(self, left, right):
        lpoint = left.point if isinstance(left, _FixedBase) else 0
        rpoint = right.point if isinstance(right, _FixedBase) else 0
        lsigned = vtypes.get_signed(left)
        rsigned = vtypes.get_signed(right)
        point = _max_mux(lpoint, rpoint)
        signed = lsigned and rsigned if not self.overwrite_signed else False
        lwidth = left.bit_length()
        rwidth = right.bit_length()

        if lpoint <= rpoint:
            ldata, rdata = adjust(left, right, lpoint, rpoint, signed)
            shift_size = point
        else:
            ldata = left
            rdata = right
            shift_size = point - (lpoint - rpoint)

        try:
            lmsb = ldata[lwidth - 1]
        except:
            lmsb = (ldata >> (lwidth - 1) & vtypes.Int(1, 1, base=2))

        try:
            rmsb = rdata[rwidth - 1]
        except:
            rmsb = (rdata >> (rwidth - 1) & vtypes.Int(1, 1, base=2))

        abs_ldata = (ldata if not lsigned else
                     vtypes.Mux(vtypes.Ulnot(lmsb), ldata, vtypes.Unot(ldata) + 1))
        abs_rdata = (rdata if not rsigned else
                     vtypes.Mux(vtypes.Ulnot(rmsb), rdata, vtypes.Unot(rdata) + 1))
        abs_data = vtypes.Divide(abs_ldata, abs_rdata)
        data = (abs_data if not signed else
                vtypes.Mux(vtypes.Eq(lmsb, rmsb),
                           abs_data, vtypes.Unot(abs_data) + 1))

        if shift_size > 0:
            data = vtypes.Sll(data, shift_size)

        _FixedSkipUnaryOperator.__init__(self, data, point, signed)


class _FixedPlus(_FixedBinaryOperator, vtypes.Plus):
    ast_name = 'Plus'

    def __init__(self, left, right):
        left, right = self.init(left, right)
        vtypes.Plus.__init__(self, left, right)


class _FixedMinus(_FixedBinaryOperator, vtypes.Minus):
    ast_name = 'Minus'

    def __init__(self, left, right):
        left, right = self.init(left, right)
        vtypes.Minus.__init__(self, left, right)


class _FixedLessThan(_FixedBinaryOperator, vtypes.LessThan):
    ast_name = 'LessThan'
    overwrite_signed = True

    def __init__(self, left, right):
        left, right = self.init(left, right)
        vtypes.LessThan.__init__(self, left, right)


class _FixedGreaterThan(_FixedBinaryOperator, vtypes.GreaterThan):
    ast_name = 'GreaterThan'

    def __init__(self, left, right):
        left, right = self.init(left, right)
        vtypes.GreaterThan.__init__(self, left, right)


class _FixedLessEq(_FixedBinaryOperator, vtypes.LessEq):
    ast_name = 'LessEq'

    def __init__(self, left, right):
        left, right = self.init(left, right)
        vtypes.LessEq.__init__(self, left, right)


class _FixedGreaterEq(_FixedBinaryOperator, vtypes.GreaterEq):
    ast_name = 'GreaterEq'

    def __init__(self, left, right):
        left, right = self.init(left, right)
        vtypes.GreaterEq.__init__(self, left, right)


class _FixedEq(_FixedBinaryOperator, vtypes.Eq):
    ast_name = 'Eq'

    def __init__(self, left, right):
        left, right = self.init(left, right)
        vtypes.Eq.__init__(self, left, right)


class _FixedNotEq(_FixedBinaryOperator, vtypes.NotEq):
    ast_name = 'NotEq'

    def __init__(self, left, right):
        left, right = self.init(left, right)
        vtypes.NotEq.__init__(self, left, right)


class _FixedUplus(_FixedUnaryOperator, vtypes.Uplus):
    ast_name = 'Uplus'
    pass


class _FixedUminus(_FixedUnaryOperator, vtypes.Uminus):
    ast_name = 'Uminus'
    pass


class _FixedConstant(_FixedBase):
    pass


class _FixedInt(_FixedConstant, vtypes.Int):
    ast_name = 'Int'

    def __init__(self, value, width=None, base=None, point=0, signed=True, raw=False):
        value = value if raw else to_fixed(value, point)
        vtypes.Int.__init__(self, value, width, base, signed)
        self.point = point
