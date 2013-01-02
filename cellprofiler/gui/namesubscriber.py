"""namesubscriber.py - implements a combobox with extra information

CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2013 Broad Institute
All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
"""
import  wx

def align_twosided_items(parent, items, min_spacing=8, left_texts=[], right_texts=[]):
    '''Find spacing for a list of pairs of text such that the left texts are
    left justified and the right texts (roughly) right justified.
    '''
    if items:
        if wx.Platform == '__WXMSW__':
            # ignore minspacing for windows
            for item, left, right in zip(items, left_texts, right_texts):
                item.SetItemLabel("%s\t%s" % (left, right))
        else:
            # Mac and linux use spaces to align.
            widths = [parent.GetTextExtent("%s%s%s" % (left, " " * min_spacing, right))[0]
                      for left, right in zip(left_texts, right_texts)]
            maxwidth = max(widths)
            spacewidth = parent.GetTextExtent("  ")[0] - parent.GetTextExtent(" ")[0]
            for item, left, right, initial_width in \
                    zip(items, left_texts, right_texts, widths):
                numspaces = int(min_spacing + (maxwidth - initial_width) / spacewidth)
                item.SetItemLabel("%s%s%s" % (left, ' ' * numspaces, right))

class NameSubcriberComboBox(wx.Panel):
    '''A read-only combobox with extra annotation, and a context menu.

    Mostly the same interface as wx.ComboBox, but choices is a list of (Name,
    Parent, modulenum).
    '''
    def __init__(self, annotation, choices=[], value='', name=''):
        wx.Panel.__init__(self, annotation, name=name)
        self.orig_choices = choices
        self.IDs = [wx.NewId() for c in choices]
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.combo_dlg = wx.ComboBox(self, choices=[name for name, _, _ in choices],
                                      value=value,
                                      style=wx.CB_READONLY)
        self.annotation_dlg = wx.StaticText(self, label='', style=wx.ST_NO_AUTORESIZE)
        self.annotation_dlg.MinSize = (max([self.annotation_dlg.GetTextExtent(annotation + " (from #00)")[0]
                                         for _, annotation, _ in self.orig_choices]),
                                       -1)
        self.update_annotation()

        sizer.AddStretchSpacer()
        sizer.Add(self.combo_dlg, flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER, border=3)
        sizer.Add((5, 5))
        sizer.Add(self.annotation_dlg, flag=wx.ALIGN_CENTER)
        sizer.AddStretchSpacer()
        self.SetSizer(sizer)

        self.combo_dlg.Bind(wx.EVT_COMBOBOX, self.choice_made)
        self.combo_dlg.Bind(wx.EVT_RIGHT_DOWN, self.right_menu)
        for child in self.combo_dlg.Children:
            # Mac implements read_only combobox as a choice in a child
            child.Bind(wx.EVT_RIGHT_DOWN, self.right_menu)
        self.Bind(wx.EVT_MENU, self.menu_selected)
        self.callbacks = []

    def choice_made(self, evt):
        choice = self.orig_choices[self.combo_dlg.Selection]
        self.update_annotation()
        for cb in self.callbacks:
            cb(evt)
        self.Refresh()

    def add_callback(self, cb):
        self.callbacks.append(cb)

    def update_annotation(self):
        self.annotation_dlg.Label = ''
        if self.orig_choices:
            ch = self.orig_choices[self.combo_dlg.Selection]
            if ch[1]:
                self.annotation_dlg.Label = '(from %s #%02d)' % (ch[1], ch[2])

    def right_menu(self, evt):
        menu = wx.Menu()
        all_menu = wx.Menu()

        choices_sorted_by_num = [c[1:] for c in sorted([(num, name, annotation, num, id)
                                                        for (name, annotation, num), id in
                                                        zip(self.orig_choices, self.IDs)])]
        for name, annotation, num, choiceid in choices_sorted_by_num:
            all_menu.Append(choiceid, "filler")

        align_twosided_items(self.combo_dlg,
                             all_menu.MenuItems,
                             left_texts=[name for name, _, _, _ in choices_sorted_by_num],
                             right_texts=["(%s #%02d)" % (annotation, num) if annotation else "" for
                                          _, annotation, num, _ in choices_sorted_by_num])

        submenus = {}
        for name, annotation, num, choiceid in choices_sorted_by_num:
            if not annotation:
                continue
            if annotation not in submenus:
                submenus[num, annotation] = wx.Menu()
            submenus[num, annotation].Append(choiceid, "%s" % name)
        menu.AppendMenu(wx.ID_ANY, "All", all_menu)
        for (num, annotation), submenu in sorted(submenus.items()):
            menu.AppendMenu(wx.ID_ANY, "filler", submenu)
        align_twosided_items(self.combo_dlg,
                             menu.MenuItems,
                             left_texts=['All'] + [annotation for num, annotation in sorted(submenus.keys())],
                             right_texts=[''] + ["#%02d" % num for num, annotation in sorted(submenus.keys())])
        self.PopupMenu(menu)
        menu.Destroy()

    def menu_selected(self, evt):
        self.combo_dlg.Selection = self.IDs.index(evt.Id)
        # fake a choice
        self.choice_made(evt)

    def GetItems(self):
        return self.orig_choices

    def SetItems(self, choices):
        self.orig_choices = choices
        current = self.Value
        self.combo_dlg.Items = [name for name, _, _ in choices]
        # on Mac, changing the items clears the current selection
        self.SetValue(current)
        self.update_annotation()
        self.Refresh()

    Items = property(GetItems, SetItems)

    def GetValue(self):
        return self.combo_dlg.Value

    def SetValue(self, value):
        self.combo_dlg.Value = value
        self.update_annotation()
        self.Refresh()

    Value = property(GetValue, SetValue)
