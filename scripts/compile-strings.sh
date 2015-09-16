#!/bin/bash
LOCALES=$*

for LOCALE in ${LOCALES}
do
    echo "./oq_irmt/i18n/"${LOCALE}".ts"
    # Note we don't use pylupdate with qt .pro file approach as it is flakey
    # about what is made available.
    lrelease-qt4 ./oq_irmt/i18n/${LOCALE}.ts
done
