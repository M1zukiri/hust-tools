
using System.Windows;

namespace GalExtractor.UI
{
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // Load plugins from the current directory
            var currentDir = System.IO.Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
            if (currentDir != null)
            {
                var pluginDir = System.IO.Path.Combine(currentDir, "Plugins");
                if (System.IO.Directory.Exists(pluginDir))
                {
                    var pluginPaths = System.IO.Directory.GetFiles(pluginDir, "*.dll");
                    // In a real implementation, you would pass these paths to the PluginManager
                    // This is just an example of how you might load plugins
                }
            }
        }
    }
}
