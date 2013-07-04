import os
import sys

from qisys import ui
import qisys.archive
import qisys.sh
import qidoc.project


class SphinxProject(qidoc.project.DocProject):
    """ A doc projet using Sphinx """
    def __init__(self, doc_worktree, project, name,
                 depends=None, dest=None):
        self.doc_type = "sphinx"
        self.examples = list()
        super(SphinxProject, self).__init__(doc_worktree, project, name,
                                            depends=depends,
                                            dest=dest)
    @property
    def source_dir(self):
        return os.path.join(self.path, "source")

    @property
    def template_project(self):
        return self.doc_worktree.template_project

    def configure(self, **kwargs):
        """ Create a correct conf.py in self.build_dir """
        in_conf_py = os.path.join(self.source_dir, "conf.in.py")
        if os.path.exists(in_conf_py):
            if not self.template_project:
                ui.warning("Found a conf.in.py but no template project found "
                           "in the worktree")
        else:
            in_conf_py = os.path.join(self.source_dir, "conf.py")
            if not os.path.exists(in_conf_py):
                ui.error("Could not find a conf.py or a conf.in.py in", self.source_dir)
                return

        with open(in_conf_py) as fp:
            conf = fp.read()

        if self.template_project:
            from_template = self.template_project.sphinx_conf
            from_template = from_template.format(**kwargs)
            conf = from_template + conf

        from_conf = dict()
        try:
            exec(conf, from_conf)
        except Exception, e:
            ui.error("Could not read", in_conf_py, "\n", e)
            return

        if "version" not in from_conf:
            if kwargs.get("version"):
                conf += '\nversion = "%s"\n' % kwargs["version"]

        if "html_theme_path" not in from_conf and self.template_project:
            conf += '\nhtml_theme_path = ["%s"]\n' % self.template_project.themes_path

        out_conf_py = os.path.join(self.build_dir, "conf.py")
        qisys.sh.write_file_if_different(conf, out_conf_py)


    def build(self, werror=False):
        """ Run sphinx.main() with the correct arguments """
        try:
            import sphinx
        except ImportError, e:
            ui.error(e, "skipping build")
            return

        if self.prebuild_script:
            ui.info(ui.green, "Running pre-build-scipt:",
                    ui.white, self.prebuild_script)
            cmd = [sys.executable, self.prebuild_script]
            qisys.command.call(cmd, cwd=self.path)
            ui.info()

        self.generate_examples_zips()

        html_dir = os.path.join(self.build_dir, "html")
        if self.template_project:
            for path in self.template_project.sys_path:
                if path not in sys.path:
                    sys.path.insert(0, path)

        cmd = [sys.executable,
               "-c", self.build_dir,
                "-b", "html"]
        if werror:
            cmd.append("-W")
        cmd.extend([self.source_dir, html_dir])
        rc = sphinx.main(argv=cmd)
        if rc != 0:
            raise SphinxBuildError(self)

    def generate_examples_zips(self):
        for example_src in self.examples:
            example_path = os.path.join(self.source_dir, example_src)
            qisys.archive.compress(example_path, algo="zip", quiet=True)

    def install(self, destdir):
        for example_src in self.examples:
            example_path = os.path.join(self.source_dir, example_src)
            real_dest = os.path.join(destdir, example_src)
            qisys.sh.install(example_path, real_dest, quiet=True)

        def non_hidden(src):
            return not src.startswith(".")

        qisys.sh.install(self.html_dir, destdir, filter_fun=non_hidden)


class SphinxBuildError(Exception):
    def __str__(self):
        return "Error occured when building doc project: %s" % self.args[0].name
