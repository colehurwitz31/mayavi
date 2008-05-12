"""The MayaVi Engine meant to be used with Envisage.
"""
# Author: Prabhu Ramachandran <prabhu_r@users.sf.net>
# Copyright (c) 2005-2007, Enthought, Inc.
# License: BSD Style.

# Standard library imports.
import logging

# Enthought library imports.
from enthought.traits.api import Instance, Bool, on_trait_change
from enthought.tvtk.plugins.scene.i_scene_manager import \
            ISceneManager
from enthought.tvtk.plugins.scene.ui.actions import NewScene
from enthought.tvtk.plugins.scene import scene_editor 
from enthought.pyface.api import GUI
from enthought.pyface.workbench.api import WorkbenchWindow

# Local imports.
from enthought.mayavi.core.scene import Scene
from enthought.mayavi.core.engine import Engine

logger = logging.getLogger()

######################################################################
# `EnvisageEngine` class
######################################################################
class EnvisageEngine(Engine):

    # The version of this class.  Used for persistence.
    __version__ = 0

    # The envisage application.
    window = Instance(WorkbenchWindow)

    ######################################################################
    # `object` interface
    ######################################################################
    def __get_pure_state__(self):
        d = self.__dict__.copy()
        for x in ['application',]:
            d.pop(x, None)
        return d    

    ######################################################################
    # `Engine` interface
    ######################################################################
    def start(self):
        """This starts the engine.  Only after the engine starts is it
        possible to use mayavi.  This particular method is called
        automatically when the window is opened."""

        if self.running:
            return
        
        # Add all the existing scenes from the scene plugin.
        scene_manager = self.window.get_service(ISceneManager)
        for scene in scene_manager.scenes:
            self.add_scene(scene)

        # Setup a handler that is invoked when a new Scene is
        # added/removed.
        scene_manager.on_trait_change(self._scene_editors_changed,
                                      'scenes_items')

        # Call the parent start method.
        super(EnvisageEngine, self).start()

        logger.debug ('--------- EnvisageEngine started ----------')

    def stop(self):
        # Call the parent stop method.
        super(EnvisageEngine, self).stop()

    def new_scene(self):
        """Creates a new VTK scene window.
        """
        action = NewScene(window=self.window)
        action.perform(None)
        
        # Flush the UI.
        GUI.process_events()
        return self.scenes[-1]

    def close_scene(self, scene):
        """Given a VTK scene instance, this method closes it.
        """
        active_window = self.window 
        s = scene.scene
        for editor in active_window.editors[:]:
            if isinstance(editor, scene_editor.SceneEditor):
                if id(editor.scene) == id(s):
                    editor.close()
                    break
        # Flush the UI.
        GUI.process_events()

    ######################################################################
    # Non-public interface
    ######################################################################
    def _scene_editors_changed(self, list_event):
        """This is called when the items of the editors trait of the
        SceneManager change.  This is used to update `self.scenes`."""
        # Remove any removed scenes.
        for scene in list_event.removed:
            self.remove_scene(scene)
        # Add any new scenes.
        for scene in list_event.added:
            self.add_scene(scene)

    @on_trait_change('window:opened')
    def _on_window_opened(self, obj, trait_name, old, new):
        """We start the engine when the window is opened."""
        if trait_name == 'opened':
            self.start()

    def _window_changed(self, old, new):
        """Static trait handler."""
        # This is needed since the service may be offered *after* the
        # window is opened in which case the _on_window_opened will do
        # nothing.
        sm = new.get_service(ISceneManager)
        if sm is not None:
            self.start()
