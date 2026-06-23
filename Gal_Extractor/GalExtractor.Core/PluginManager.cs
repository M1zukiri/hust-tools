
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;

namespace GalExtractor.Core
{
    /// <summary>
    /// Manages loading and discovery of game archive parser plugins
    /// </summary>
    public class PluginManager
    {
        private readonly List<IGameArchive> _parsers;

        public PluginManager()
        {
            _parsers = new List<IGameArchive>();
        }

        /// <summary>
        /// Gets all loaded parsers
        /// </summary>
        public IReadOnlyList<IGameArchive> Parsers => _parsers.AsReadOnly();

        /// <summary>
        /// Loads all plugins from the current assembly and optionally from external plugin assemblies
        /// </summary>
        /// <param name="pluginAssemblies">Optional assemblies to scan for plugins</param>
        public void LoadPlugins(params Assembly[] pluginAssemblies)
        {
            // Always scan the current assembly (Core)
            LoadFromAssembly(Assembly.GetExecutingAssembly());

            // Scan additional assemblies that were explicitly passed
            foreach (var assembly in pluginAssemblies)
            {
                if (assembly != null)
                {
                    LoadFromAssembly(assembly);
                }
            }
        }

        /// <summary>
        /// Legacy overload: loads plugins from external assembly file paths
        /// </summary>
        [Obsolete("Use LoadPlugins(Assembly[]) instead")]
        public void LoadPluginsFromPaths(params string[] pluginPaths)
        {
            foreach (var path in pluginPaths)
            {
                try
                {
                    if (File.Exists(path))
                    {
                        var assembly = Assembly.LoadFrom(path);
                        LoadFromAssembly(assembly);
                    }
                }
                catch (Exception ex)
                {
                    // Log or handle the exception as needed
                    Console.WriteLine($"Failed to load plugin from {path}: {ex.Message}");
                }
            }
        }

        /// <summary>
        /// Loads plugins from a specific assembly
        /// </summary>
        /// <param name="assembly">The assembly to load plugins from</param>
        private void LoadFromAssembly(Assembly assembly)
        {
            try
            {
                var types = assembly.GetTypes()
                    .Where(t => t.IsClass && !t.IsAbstract && typeof(IGameArchive).IsAssignableFrom(t));

                foreach (var type in types)
                {
                    try
                    {
                        var parser = (IGameArchive)Activator.CreateInstance(type)!;
                        _parsers.Add(parser);
                    }
                    catch (Exception ex)
                    {
                        // Log or handle the exception as needed
                        Console.WriteLine($"Failed to create instance of {type.Name}: {ex.Message}");
                    }
                }
            }
            catch (Exception ex)
            {
                // Log or handle the exception as needed
                Console.WriteLine($"Failed to load plugins from assembly {assembly.FullName}: {ex.Message}");
            }
        }

        /// <summary>
        /// Attempts to find a suitable parser for the given file stream
        /// </summary>
        /// <param name="stream">The file stream to check</param>
        /// <returns>A suitable parser if found, null otherwise</returns>
        public IGameArchive? FindParser(Stream stream)
        {
            if (stream == null || !stream.CanRead)
                return null;

            // Store the original position
            long originalPosition = stream.Position;

            try
            {
                foreach (var parser in _parsers)
                {
                    try
                    {
                        if (parser.TryOpen(stream))
                        {
                            // Reset position before returning
                            stream.Position = originalPosition;
                            return parser;
                        }
                    }
                    catch
                    {
                        // Ignore exceptions from individual parsers and continue
                    }
                    finally
                    {
                        // Reset position for the next parser
                        stream.Position = originalPosition;
                    }
                }
            }
            finally
            {
                // Ensure position is reset even if an exception occurs
                stream.Position = originalPosition;
            }

            return null;
        }

        /// <summary>
        /// Gets all supported file extensions from all loaded parsers
        /// </summary>
        /// <returns>A list of supported file extensions</returns>
        public string[] GetSupportedExtensions()
        {
            return _parsers
                .SelectMany(p => p.SupportedExtensions)
                .Distinct()
                .ToArray();
        }
    }
}