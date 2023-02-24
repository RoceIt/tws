#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#
import decimal

from roc_settings import Error
import roc_decimal as r_dcm
import validate

class CurrencyError(Error): pass

class Currency(decimal.Decimal):
    
    symbol = '0'
    short_name = 'ZERO'
    full_name = 'zeronullniks'
    minimal_str_exponent = 0
    
    def __new__(cls, value):
        if isinstance(value, Currency):
            inst = value.convert_to(cls)
        else:
            try:
                inst = super().__new__(cls, str(value))
            except Exception:
                print(value, ' | ', str(value))
        return inst
        
    def __repr__(self):
        t = ''.join([str(self.__class__.__qualname__), 
                     '(', super().__str__(), ')'])
        return t
    
    def __str__(self):
        av = self.quantize(decimal.Decimal(10) ** -self.minimal_str_exponent)
        if av == self:
            nt = str(av)
        else:
            nt = super().__str__()
        t = ' '.join([self.symbol, nt])
        return t
    
    def __add__(self, other):
        """Returns self + other.
        
        Self and other must be the same currency.  If not TypeError
        is raised.
        """
        if self.__class__ is not other.__class__:
            mss = ('unsupported operand types(s) for +: {} and {}'.
                   format(self.__class__.__name__, other.__class__.__name__))
            raise TypeError(mss)
        return self.__class__(super().__add__(other))    
    
    def __sub__(self, other):
        """Returns self - other.
        
        Self and other must be the same currency.  If not TypeError
        is raised.
        """
        if self.__class__ is not other.__class__:
            mss = ('unsupported operand types(s) for +: {} and {}'.
                   format(self.__class__.__name__, other.__class__.__name__))
            raise TypeError(mss)
        return self.__class__(super().__sub__(other))
    
    def __mul__(self, other):
        """Returns self * other.
        
        They can not both be a currency. You can not multiply
        currencies.
        """
        validate.as_int_or_float(other)
        other = decimal.Decimal(str(other))
        return self.__class__(super().__mul__(other))
    __rmul__ = __mul__
    
    def __truediv__(self, other):
        """Returns self * other.
        
        They can not both be a currency. You can not multiply
        currencies.
        """
        validate.as_int_or_float(other)
        if other == 0:
            raise ZeroDivisionError()
        return self.__class__(super().__truediv__(other))
    
    def __rtruediv__(self, other):
        """Should not be allowed."""
        raise TypeError('Currency not allowed as denominator')
    
    def round_up_to(self, round_to):
        """ Returns first number away from zero that is a 
        multiplier of round_to.
        """
        m = r_dcm.round_to_nearest(self, round_to, r_dcm.ROUND_UP)
        return self.__class__(m)
    
    def round_down_to(self, round_to):
        """ Returns first number closer to zero that is a 
        multiplier of round_to.
        """
        m = r_dcm.round_to_nearest(self, round_to, r_dcm.ROUND_DOWN)
        return self.__class__(m)
        
    def convert_to(self, new_currency, as_trade=False):
        return convert(self, new_currency, as_trade)

class euro_(Currency):
    symbol = '€'
    short_name = 'EUR'
    full_name = 'euro'
    minimal_str_exponent = 2

class US_dollar_(Currency):
    symbol = '$'
    short_name = 'USD'
    full_name = 'US-dollar'
    minimal_str_exponent = 2
    
class point_(Currency):
    symbol = 'p'
    short_name = 'PNT'
    full_name = 'point'
    minimal_str_exponent = 2
  
            
def convert(value, new_currency, as_trade=False):
    if not issubclass(new_currency, Currency):
        raise CurrencyError('undefined currency: {}'.format(str(Currency)))
    if not isinstance(value, Currency):
        raise CurrencyError('value to convert must be a Currency, '
                            'wrong type: {}'.format(type(value)))        
    if as_trade: 
        raise NotImplemented('convert as trade not implemented')
    # just for testing should work with a matrix, db or live?
    if isinstance(value, new_currency):
        return value
    if isinstance(value, euro_) and new_currency == US_dollar_:
        new_value = decimal.Decimal(value) * decimal.Decimal('1.35')
        return US_dollar_(new_value)
    if isinstance(value, US_dollar_) and new_currency == euro_:
        return euro_(decimal.Decimal(value) * decimal.Decimal('1.35') ** -1)
    raise CurrencyError('Undefined conversion: ')

def to_currency(string):
    """Returns the currentie defined by the string.
    """
    try:
        currency, value = string.split()
        if value in _currency_translation_list:
            currency, value = value, currency
        currency = _currency_translation_list[currency.upper()]
        value = decimal.Decimal(value)
    except (ValueError, KeyError):
        raise Error('invalid currency string')
    return currency(value)
    
    
translators = {k: v for k, v in locals().items()
              if isinstance(v, type) and issubclass(v, Currency)}
translators.pop('Currency')
_currency_translation_list = dict()
for k, v in translators.items():
    try:
        symbol = v.symbol.upper()
        short_name = v.short_name.upper()
        full_name = v.full_name.upper()
        key = k.upper()
        if (symbol in _currency_translation_list
            or
            short_name in _currency_translation_list
            or
            full_name in _currency_translation_list
        ):
            mss = 'symbol, short_name_ or full_name not unique in {}'.format(k)
            raise Error(mss)
    except Exception:
        print ('wrong currency definition, check roc_currency.')
        raise
    if (symbol in _currency_translation_list
        or
        short_name in _currency_translation_list
        or
        full_name in _currency_translation_list
    ):
        raise Error()
    _currency_translation_list[symbol] = v
    _currency_translation_list[short_name] = v
    _currency_translation_list[full_name] = v
    _currency_translation_list[key] = v
    