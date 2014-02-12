/*******************************************************************************
    Creme is a free/open-source Customer Relationship Management software
    Copyright (C) 2009-2014  Hybird

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*******************************************************************************/

creme.layout = creme.layout || {}

creme.layout.TextAreaAutoSize = creme.component.Component.sub({
    _init_: function() {
        this._listeners = $.proxy(this._onResize, this);
    },

    _onResize: function(e)
    {
        var element = this._delegate;
        var previous = this._count !== undefined ? this._count : this._initial;
        var count = this._count = element.val() ? element.val().split('\n').length: this._initial;

        if (e.keyCode === 13)
            ++count;

        if (previous !== count)
        {
            element.get().scrollTop = 0;
            element.attr('rows', count);
        }
    },

    bind: function(element)
    {
        var self = this;

        if (this._delegate !== undefined)
            throw new Error('already bound');

        this._delegate = element;
        element.css({'overflow-y':'hidden', 'resize': 'none'})

        this._initial = parseInt(element.attr('rows')) || 1;
        this._onResize(element);

        element.bind('propertychange keydown paste input', this._listeners);
        return this;
    },

    unbind: function()
    {
        if (this._delegate === undefined)
            throw new Error('not bound');

        this._delegate.unbind('propertychange keyup paste', this._listeners);
        this._delegate = undefined;

        return this;
    }
});