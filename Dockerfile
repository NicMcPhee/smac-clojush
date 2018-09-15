FROM dstelljes/smac:2.10

RUN dnf install -y bzip2 gcc gcc-c++ git make python tar

WORKDIR /
ADD http://www.cril.univ-artois.fr/~roussel/runsolver/runsolver-3.3.5.tar.bz2 ./
RUN tar -jxf runsolver*.tar.bz2
RUN rm -f runsolver*.tar.bz2
RUN mv runsolver runsolver-3.3.5
WORKDIR /runsolver-3.3.5/src
RUN sed -i -r 's/^(CFLAGS.*)$/\1 -std=gnu++98/' Makefile
RUN make
RUN mv runsolver /runsolver
WORKDIR /
RUN rm -rf /runsolver-3.3.5

ADD https://raw.githubusercontent.com/technomancy/leiningen/stable/bin/lein /usr/bin/lein
RUN chmod +x /usr/bin/lein
RUN git clone https://github.com/lspector/Clojush.git clojush
WORKDIR /clojush
RUN lein uberjar
RUN cp target/clojush-*-standalone.jar /clojush-standalone.jar
WORKDIR /
RUN rm -rf /clojush /root/.lein /usr/bin/lein

ADD * ./
RUN ln -s /usr/bin/smac smac
RUN mkdir smac-output

RUN dnf remove -y bzip2 gcc gcc-c++ git make tar
RUN dnf clean all

VOLUME /smac-output
