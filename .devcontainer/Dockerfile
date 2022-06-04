# see https://hub.docker.com/r/wolframresearch/wolframengine
# Activate Using Node-Locked Licensing
FROM wolframresearch/wolframengine:13.0

# # Install needed packages and setup non-root user. Use a separate RUN statement to add your own dependencies.
RUN echo ${WOLFRAM_mathpass} 
RUN ls -R ~/.WolframEngine
# > ~/.WolframEngine/Licensing/mathpass

# RUN ap
# RUN yes | unminimize 2>&1 \ 
#     && bash /tmp/library-scripts/common-debian.sh "${INSTALL_ZSH}" "${USERNAME}" "${USER_UID}" "${USER_GID}" "${UPGRADE_PACKAGES}" "true" "false" \
#     && apt-get clean -y && rm -rf /var/lib/apt/lists/* /tmp/library-scripts