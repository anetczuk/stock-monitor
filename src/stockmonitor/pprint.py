# MIT License
#
# Copyright (c) 2021 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


def pprint(variable, indent=0):
    if variable is None:
        print('\t' * indent + "None")
        return
    if not variable:
        ## empty container
        print('\t' * indent + "Empty")
        return

    if isinstance( variable, dict ):
        for key, value in variable.items():
            print('\t' * indent + str(key) + ":")
            pprint( value, indent + 1 )
    elif isinstance( variable, list ):
        # pylint: disable=C0200
        for i in range(0, len(variable)):
            value = variable[i]
            print('\t' * indent + "[" + str(i) + "]:")
            pprint( value, indent + 1 )
    else:
        print('\t' * (indent + 1) + str(variable))
